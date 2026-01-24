from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_module():
    module_path = (
        Path(__file__).resolve().parents[2]
        / "backend"
        / "tower"
        / "apps"
        / "chunk-storage"
        / "main.py"
    )
    spec = spec_from_file_location("chunk_storage", module_path)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FakeWriter:
    def __init__(self) -> None:
        self.records = []

    def upsert_chunks(self, records):
        self.records.extend(records)


def test_chunk_storage_builds_records():
    module = _load_module()
    event = {
        "document_id": "doc-123",
        "chunks": [
            {"page_number": 1, "content": "alpha"},
            {"page_number": 2, "content": "beta"},
        ],
    }
    writer = FakeWriter()

    result = module.handle_chunks(event, writer)

    assert result["status"] == "ok"
    assert len(writer.records) == 2
    assert writer.records[0]["document_id"] == "doc-123"
