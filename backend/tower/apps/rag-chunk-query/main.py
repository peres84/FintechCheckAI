from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol
from urllib.request import Request, urlopen

import re


def _tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if token}


def retrieve_chunks(query: str, chunks: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
    query_tokens = _tokenize(query)
    scored = []
    for chunk in chunks:
        chunk_tokens = _tokenize(chunk.get("content", ""))
        if not chunk_tokens:
            score = 0.0
        else:
            score = len(query_tokens & chunk_tokens) / max(len(query_tokens), 1)
        scored.append({**chunk, "score": score})

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


class ChunkStore(Protocol):
    def upsert(self, records: list[dict[str, Any]]) -> Any: ...
    def read_all(self) -> list[dict[str, Any]]: ...


def _load_chunks(event: dict[str, Any]) -> list[dict[str, Any]]:
    if "chunks" in event:
        return event["chunks"]
    if "chunks_path" in event and event["chunks_path"]:
        data = json.loads(Path(event["chunks_path"]).read_text(encoding="utf-8"))
        return data.get("pages", [])
    if "chunks_url" in event and event["chunks_url"]:
        request = Request(event["chunks_url"], headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data.get("pages", [])
    raise ValueError("Missing chunks, chunks_path, or chunks_url")


def _build_chunk_records(event: dict[str, Any]) -> list[dict[str, Any]]:
    document_id = event["document_id"]
    created_at = datetime.utcnow()
    records: list[dict[str, Any]] = []
    for chunk in _load_chunks(event):
        records.append(
            {
                "chunk_id": chunk.get("chunk_id") or str(uuid.uuid4()),
                "document_id": document_id,
                "page_number": chunk.get("page_number") or chunk.get("page") or 0,
                "content": chunk.get("content") or chunk.get("text") or "",
                "embedding": chunk.get("embedding") or [],
                "created_at": created_at,
            }
        )
    return records


def _table_to_records(table_data: Any) -> list[dict[str, Any]]:
    for method_name in ("to_dicts", "to_pylist"):
        method = getattr(table_data, method_name, None)
        if callable(method):
            return method()
    iter_rows = getattr(table_data, "iter_rows", None)
    if callable(iter_rows):
        return list(iter_rows(named=True))
    return list(table_data)


def handle_event(
    event: dict[str, Any],
    store: ChunkStore,
    rag_fn=retrieve_chunks,
) -> dict[str, Any]:
    records = _build_chunk_records(event)
    if not event.get("dry_run", False) and records:
        store.upsert(records)

    chunks = store.read_all()
    results = rag_fn(event["query"], chunks, top_k=event.get("top_k", 5))
    return {"status": "ok", "stored": len(records), "results": results}


class TowerChunkStore:
    def __init__(self, catalog: str | None = None, namespace: str | None = None) -> None:
        import pyarrow as pa
        import tower

        self._schema = pa.schema(
            [
                ("chunk_id", pa.string()),
                ("document_id", pa.string()),
                ("page_number", pa.int32()),
                ("content", pa.large_string()),
                ("embedding", pa.list_(pa.float32())),
                ("created_at", pa.timestamp("ms")),
            ]
        )
        catalog_name = catalog or "database_catalog"
        namespace = namespace or "default"
        self._table = tower.tables(
            "chunks",
            catalog=catalog_name,
            namespace=namespace,
        ).create_if_not_exists(self._schema)

    def upsert(self, records: list[dict[str, Any]]) -> Any:
        import pyarrow as pa

        table = pa.Table.from_pylist(records, schema=self._schema)
        return self._table.upsert(table, join_cols=["document_id", "page_number"])

    def read_all(self) -> list[dict[str, Any]]:
        table_obj = self._table
        if hasattr(table_obj, "load"):
            table_obj = table_obj.load()
        if hasattr(table_obj, "read"):
            table_obj = table_obj.read()
        return _table_to_records(table_obj)


def _env_event() -> dict[str, Any]:
    document_id = os.getenv("DOCUMENT_ID")
    if not document_id:
        raise ValueError("DOCUMENT_ID is required")
    query = os.getenv("QUERY")
    if not query:
        raise ValueError("QUERY is required")
    chunks_path = os.getenv("CHUNKS_PATH")
    chunks_url = os.getenv("CHUNKS_URL")
    if not chunks_path and not chunks_url:
        raise ValueError("CHUNKS_PATH or CHUNKS_URL is required")
    top_k = int(os.getenv("TOP_K", "5"))
    return {
        "document_id": document_id,
        "query": query,
        "top_k": top_k,
        "chunks_path": chunks_path,
        "chunks_url": chunks_url,
        "catalog": os.getenv("CATALOG", "database_catalog"),
        "namespace": os.getenv("NAMESPACE", "default"),
        "dry_run": os.getenv("DRY_RUN", "false").lower() in {"1", "true", "yes"},
    }


def handler(event, context):
    store = TowerChunkStore(
        catalog=event.get("catalog"),
        namespace=event.get("namespace"),
    )
    return handle_event(event, store)


def main() -> None:
    event = _env_event()
    store = TowerChunkStore(
        catalog=event.get("catalog"),
        namespace=event.get("namespace"),
    )
    result = handle_event(event, store)
    print(result)


if __name__ == "__main__":
    main()
