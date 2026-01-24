from __future__ import annotations

from typing import Any, Protocol


class TowerClientLike(Protocol):
    def execute_sql(self, sql: str, params: dict[str, Any] | None = None) -> Any: ...


class TowerService:
    def __init__(self, client: TowerClientLike | None = None) -> None:
        if client is None:
            try:
                from tower_sdk import TowerClient  # type: ignore
            except Exception as exc:
                raise RuntimeError(f"Tower SDK unavailable: {exc}") from exc
            client = TowerClient()
        self._client = client

    def insert_document(self, record: dict[str, Any]) -> Any:
        sql = (
            "INSERT INTO documents "
            "(document_id, company_id, version, sha256, source_url, created_at) "
            "VALUES (:document_id, :company_id, :version, :sha256, :source_url, :created_at)"
        )
        return self._client.execute_sql(sql, record)

    def insert_chunks(self, records: list[dict[str, Any]]) -> Any:
        sql = (
            "INSERT INTO chunks "
            "(chunk_id, document_id, page_number, content, embedding, created_at) "
            "VALUES (:chunk_id, :document_id, :page_number, :content, :embedding, :created_at)"
        )
        results = []
        for record in records:
            results.append(self._client.execute_sql(sql, record))
        return results
