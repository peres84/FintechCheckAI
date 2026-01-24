from __future__ import annotations

import json
import os
import uuid
from urllib.request import Request, urlopen
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol


class ChunkWriter(Protocol):
    def upsert_chunks(self, records: list[dict[str, Any]]) -> Any: ...


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
    raise ValueError("Missing chunks or chunks_path")


def _build_chunk_records(event: dict[str, Any]) -> list[dict[str, Any]]:
    document_id = event["document_id"]
    created_at = datetime.utcnow()
    records = []
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


def handle_chunks(event: dict[str, Any], writer: ChunkWriter) -> dict[str, Any]:
    records = _build_chunk_records(event)

    if not event.get("dry_run", False) and records:
        writer.upsert_chunks(records)

    return {"status": "ok", "chunks": records}


class TowerChunkWriter:
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
        # Use the catalog configured in Tower Team Settings (database_catalog)
        catalog_name = catalog or "database_catalog"
        namespace = namespace or "default"
        self._table = tower.tables(
            "chunks",
            catalog=catalog_name,
            namespace=namespace,
        ).create_if_not_exists(self._schema)

    def upsert_chunks(self, records: list[dict[str, Any]]) -> Any:
        import pyarrow as pa

        table = pa.Table.from_pylist(records, schema=self._schema)
        return self._table.upsert(table, join_cols=["document_id", "page_number"])


def _env_event() -> dict[str, Any]:
    document_id = os.getenv("DOCUMENT_ID")
    if not document_id:
        raise ValueError("DOCUMENT_ID is required")
    chunks_path = os.getenv("CHUNKS_PATH")
    chunks_url = os.getenv("CHUNKS_URL")
    if not chunks_path and not chunks_url:
        raise ValueError("CHUNKS_PATH or CHUNKS_URL is required")
    return {
        "document_id": document_id,
        "chunks_path": chunks_path,
        "chunks_url": chunks_url,
        "catalog": os.getenv("CATALOG", "database_catalog"),
        "namespace": os.getenv("NAMESPACE", "default"),
        "dry_run": os.getenv("DRY_RUN", "false").lower() in {"1", "true", "yes"},
    }


def handler(event, context):
    writer = TowerChunkWriter(
        catalog=event.get("catalog"),
        namespace=event.get("namespace"),
    )
    return handle_chunks(event, writer)


def main() -> None:
    event = _env_event()
    writer = TowerChunkWriter(
        catalog=event.get("catalog"),
        namespace=event.get("namespace"),
    )
    result = handle_chunks(event, writer)
    print(result)


if __name__ == "__main__":
    main()
