from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from typing import Any, Protocol

import pyarrow as pa
import tower


def _table_to_records(table_data: Any) -> list[dict[str, Any]]:
    """Convert table data to list of dictionaries."""
    for method_name in ("to_dicts", "to_pylist"):
        method = getattr(table_data, method_name, None)
        if callable(method):
            return method()
    iter_rows = getattr(table_data, "iter_rows", None)
    if callable(iter_rows):
        return list(iter_rows(named=True))
    return list(table_data)


class TowerVerificationStore:
    """Store for verification logs in Tower."""
    
    def __init__(self, catalog: str | None = None, namespace: str | None = None) -> None:
        self._schema = pa.schema(
            [
                ("verification_id", pa.string()),
                ("youtube_url", pa.string()),
                ("company_id", pa.string()),
                ("verdict", pa.string()),
                ("created_at", pa.timestamp("ms")),
            ]
        )
        catalog_name = catalog or "database_catalog"
        namespace_name = namespace or "default"
        self._table = tower.tables(
            "verifications",
            catalog=catalog_name,
            namespace=namespace_name,
        ).create_if_not_exists(self._schema)

    def insert_verification(self, record: dict[str, Any]) -> Any:
        """Insert a verification record."""
        table = pa.Table.from_pylist([record], schema=self._schema)
        return self._table.upsert(table, join_cols=["verification_id"])

    def get_verifications_by_company(self, company_id: str) -> list[dict[str, Any]]:
        """Get all verifications for a company."""
        # Note: Tower may not support WHERE clauses directly
        # This is a simplified version - in production, you'd use SQL queries
        table_obj = self._table
        if hasattr(table_obj, "load"):
            table_obj = table_obj.load()
        if hasattr(table_obj, "read"):
            table_obj = table_obj.read()
        
        all_records = _table_to_records(table_obj)
        return [r for r in all_records if r.get("company_id") == company_id]

    def get_verifications_by_url(self, youtube_url: str) -> list[dict[str, Any]]:
        """Get all verifications for a YouTube URL."""
        table_obj = self._table
        if hasattr(table_obj, "load"):
            table_obj = table_obj.load()
        if hasattr(table_obj, "read"):
            table_obj = table_obj.read()
        
        all_records = _table_to_records(table_obj)
        return [r for r in all_records if r.get("youtube_url") == youtube_url]


def _build_verification_record(event: dict[str, Any]) -> dict[str, Any]:
    """Build verification record from event."""
    verification_id = event.get("verification_id") or str(uuid.uuid4())
    youtube_url = event.get("youtube_url", "")
    company_id = event.get("company_id", "")
    verdict = event.get("verdict", "UNKNOWN")
    created_at = event.get("created_at") or datetime.utcnow()
    
    if isinstance(created_at, str):
        # Parse ISO format string
        created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    
    return {
        "verification_id": verification_id,
        "youtube_url": youtube_url,
        "company_id": company_id,
        "verdict": verdict,
        "created_at": created_at,
    }


def handle_event(
    event: dict[str, Any],
    store: TowerVerificationStore,
) -> dict[str, Any]:
    """
    Handle verification log event.
    
    Args:
        event: Event dictionary with verification data
        store: Tower verification store
        
    Returns:
        Result dictionary with status and verification_id
    """
    record = _build_verification_record(event)
    
    if not event.get("dry_run", False):
        store.insert_verification(record)
    
    return {
        "status": "ok",
        "verification_id": record["verification_id"],
        "stored": not event.get("dry_run", False),
    }


def handler(event, context):
    """Tower app handler."""
    store = TowerVerificationStore(
        catalog=event.get("catalog"),
        namespace=event.get("namespace"),
    )
    return handle_event(event, store)


def _env_event() -> dict[str, Any]:
    """Build event from environment variables."""
    verification_id = os.getenv("VERIFICATION_ID")
    youtube_url = os.getenv("YOUTUBE_URL", "")
    company_id = os.getenv("COMPANY_ID", "")
    verdict = os.getenv("VERDICT", "UNKNOWN")
    
    if not youtube_url and not company_id:
        raise ValueError("YOUTUBE_URL or COMPANY_ID is required")
    
    return {
        "verification_id": verification_id,
        "youtube_url": youtube_url,
        "company_id": company_id,
        "verdict": verdict,
        "catalog": os.getenv("CATALOG", "database_catalog"),
        "namespace": os.getenv("NAMESPACE", "default"),
        "dry_run": os.getenv("DRY_RUN", "false").lower() in {"1", "true", "yes"},
    }


def main() -> None:
    """Main entry point for local execution."""
    event = _env_event()
    store = TowerVerificationStore(
        catalog=event.get("catalog"),
        namespace=event.get("namespace"),
    )
    result = handle_event(event, store)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
