from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_module():
    module_path = (
        Path(__file__).resolve().parents[2]
        / "backend"
        / "tower"
        / "apps"
        / "rag-chunk-query"
        / "main.py"
    )
    spec = spec_from_file_location("rag_chunk_query", module_path)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FakeStore:
    def __init__(self, existing=None):
        self.records = []
        self._existing = existing or []

    def upsert(self, records):
        self.records.extend(records)

    def read_all(self):
        return list(self._existing)


def test_rag_chunk_query_stores_and_queries():
    module = _load_module()
    event = {
        "document_id": "doc-123",
        "query": "alpha",
        "top_k": 2,
        "chunks": [
            {"page_number": 1, "content": "alpha beta"},
            {"page_number": 2, "content": "gamma delta"},
        ],
    }
    store = FakeStore(
        existing=[
            {"chunk_id": "chunk-1", "content": "alpha beta"},
            {"chunk_id": "chunk-2", "content": "gamma delta"},
        ]
    )

    def fake_rag(query, chunks, top_k=5):
        return [{"query": query, "top_k": top_k, "count": len(chunks)}]

    result = module.handle_event(event, store, rag_fn=fake_rag)

    assert result["status"] == "ok"
    assert result["stored"] == 2
    assert store.records[0]["document_id"] == "doc-123"
    assert result["results"][0]["query"] == "alpha"
