import base64
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_module():
    module_path = (
        Path(__file__).resolve().parents[2]
        / "backend"
        / "tower"
        / "apps"
        / "document-ingestion"
        / "main.py"
    )
    spec = spec_from_file_location("document_ingestion", module_path)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FakeWriter:
    def __init__(self) -> None:
        self.records = []

    def upsert_document(self, record):
        self.records.append(record)


def test_document_ingestion_hash_and_insert():
    module = _load_module()
    pdf_bytes = b"sample-pdf"
    event = {
        "company_id": "duolingo",
        "version": "q3-2025",
        "pdf_base64": base64.b64encode(pdf_bytes).decode("utf-8"),
    }
    writer = FakeWriter()

    result = module.handle_ingestion(event, writer)

    assert result["status"] == "ok"
    assert writer.records
    assert writer.records[0]["sha256"] == (
        "ec64ca2459288e726d8d4184536cdb772c053695b9cf05efdb9a9eb8d9b0e42f"
    )
