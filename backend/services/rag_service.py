from __future__ import annotations

import re
from typing import Any


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


def verify_claims(payload: dict[str, Any]) -> dict[str, Any]:
    query = payload["query"]
    chunks = payload.get("chunks", [])
    top_k = payload.get("top_k", 5)
    return {"query": query, "chunks": retrieve_chunks(query, chunks, top_k)}
