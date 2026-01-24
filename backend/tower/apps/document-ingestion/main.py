from __future__ import annotations

import base64
import hashlib
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from urllib.request import Request, urlopen


class DocumentWriter(Protocol):
    def upsert_document(self, record: dict[str, Any]) -> Any: ...


def _decode_pdf(event: dict[str, Any]) -> bytes:
    pdf_path = event.get("pdf_path")
    if pdf_path:
        path = Path(pdf_path)
        if path.exists():
            return path.read_bytes()
    if "pdf_url" in event and event["pdf_url"]:
        timeout = int(event.get("fetch_timeout", 300))  # Increased default to 5 minutes
        request = Request(
            event["pdf_url"],
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        )
        with urlopen(request, timeout=timeout) as response:
            return response.read()
    if "pdf_base64" in event:
        return base64.b64decode(event["pdf_base64"])
    if "pdf_bytes" in event and isinstance(event["pdf_bytes"], bytes):
        return event["pdf_bytes"]
    raise ValueError("Missing pdf_path, pdf_url, pdf_base64, or pdf_bytes")


def _build_document_record(event: dict[str, Any], pdf_bytes: bytes) -> dict[str, Any]:
    sha256 = hashlib.sha256(pdf_bytes).hexdigest()
    return {
        "document_id": event.get("document_id") or str(uuid.uuid4()),
        "company_id": event["company_id"],
        "version": event.get("version", "v1"),
        "sha256": sha256,
        "source_url": event.get("source_url"),
        "created_at": datetime.utcnow(),
    }


def handle_ingestion(event: dict[str, Any], writer: DocumentWriter) -> dict[str, Any]:
    pdf_bytes = _decode_pdf(event)
    record = _build_document_record(event, pdf_bytes)

    if not event.get("dry_run", False):
        writer.upsert_document(record)

    return {"status": "ok", "document": record}


class TowerDocumentWriter:
    def __init__(self, catalog: str | None = None, namespace: str | None = None) -> None:
        import pyarrow as pa
        import tower

        schema = pa.schema(
            [
                ("document_id", pa.string()),
                ("company_id", pa.string()),
                ("version", pa.string()),
                ("sha256", pa.string()),
                ("source_url", pa.string()),
                ("created_at", pa.timestamp("ms")),
            ]
        )
        # Use the catalog configured in Tower Team Settings (database_catalog)
        catalog_name = catalog or "database_catalog"
        namespace = namespace or "default"
        self._table = tower.tables(
            "documents",
            catalog=catalog_name,
            namespace=namespace,
        ).create_if_not_exists(schema)

    def upsert_document(self, record: dict[str, Any]) -> Any:
        import pyarrow as pa

        table = pa.Table.from_pylist([record])
        return self._table.upsert(table, join_cols=["company_id", "sha256"])


def _env_event() -> dict[str, Any]:
    pdf_path = os.getenv("PDF_PATH") or ""
    pdf_url = os.getenv("PDF_URL")
    if not pdf_path and not pdf_url:
        raise ValueError("PDF_PATH or PDF_URL is required")
    company_id = os.getenv("COMPANY_ID")
    if not company_id:
        raise ValueError("COMPANY_ID is required")
    return {
        "pdf_path": pdf_path,
        "pdf_url": pdf_url,
        "company_id": company_id,
        "version": os.getenv("VERSION", "v1"),
        "source_url": os.getenv("SOURCE_URL"),
        "catalog": os.getenv("CATALOG", "database_catalog"),
        "namespace": os.getenv("NAMESPACE", "default"),
        "fetch_timeout": os.getenv("PDF_FETCH_TIMEOUT", "60"),
        "dry_run": os.getenv("DRY_RUN", "false").lower() in {"1", "true", "yes"},
    }


def handler(event, context):
    writer = TowerDocumentWriter(
        catalog=event.get("catalog"),
        namespace=event.get("namespace"),
    )
    return handle_ingestion(event, writer)


def main() -> None:
    import os
    
    event = _env_event()
    pdf_bytes = _decode_pdf(event)
    record = _build_document_record(event, pdf_bytes)
    
    print(f"✅ Document prepared:")
    print(f"  ID: {record['document_id']}")
    print(f"  Company: {record['company_id']}")
    print(f"  SHA256: {record['sha256']}")
    print(f"  Bytes: {len(pdf_bytes)}")
    
    # Check catalog environment
    catalog_name = event.get("catalog") or "database_catalog"
    namespace_name = event.get("namespace") or "default"
    
    print(f"\n🔍 Catalog Configuration Check:")
    print(f"  Catalog name: {catalog_name}")
    print(f"  Namespace: {namespace_name}")
    
    # Check all possible environment variables
    env_vars_to_check = [
        f"PYICEBERG_CATALOG__{catalog_name.upper()}__URI",
        "PYICEBERG_CATALOG__DATABASE_CATALOG__URI",
        "PYICEBERG_CATALOG__DEFAULT__URI",
        "PYICEBERG_WAREHOUSE",
    ]
    
    print(f"\n  Environment Variables:")
    for var in env_vars_to_check:
        value = os.getenv(var)
        print(f"    {var}: {'✅ ' + ('*' * 10) if value else '❌'}")
    
    # Try to write to Tower
    try:
        writer = TowerDocumentWriter(
            catalog=event.get("catalog"),
            namespace=event.get("namespace"),
        )
        result = handle_ingestion(event, writer)
        print(f"\n✅ Document stored in Tower!")
        print(result)
    except Exception as e:
        print(f"\n⚠️  Tower write failed: {type(e).__name__}: {e}")
        print(f"\nIMPORTANT: To fix this, check your Tower Catalog Configuration:")
        print(f"  1. Go to: https://app.tower.dev/hackathon_berlin/settings/catalogs")
        print(f"  2. Click on catalog '{catalog_name}'")
        print(f"  3. Verify it has:")
        print(f"     - URI (e.g., s3://bucket/warehouse or file:///path/warehouse)")
        print(f"     - Provider type (S3, GCS, Azure, or Local)")
        print(f"     - Credentials (if cloud storage)")
        print(f"\nDocument metadata that would be stored:")
        import json
        print(json.dumps(record, default=str, indent=2))


if __name__ == "__main__":
    main()
