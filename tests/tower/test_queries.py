from backend.services.tower_service import TowerService


class FakeClient:
    def __init__(self) -> None:
        self.calls = []

    def execute_sql(self, sql, params=None):
        self.calls.append((sql, params))
        return {"ok": True}


def test_tower_service_inserts_document():
    client = FakeClient()
    service = TowerService(client=client)
    record = {
        "document_id": "doc-1",
        "company_id": "duolingo",
        "version": "q3",
        "sha256": "hash",
        "source_url": None,
        "created_at": "2026-01-24T00:00:00Z",
    }

    service.insert_document(record)

    assert client.calls
    assert "INSERT INTO documents" in client.calls[0][0]


def test_tower_service_inserts_chunks():
    client = FakeClient()
    service = TowerService(client=client)
    records = [
        {
            "chunk_id": "chunk-1",
            "document_id": "doc-1",
            "page_number": 1,
            "content": "alpha",
            "embedding": None,
            "created_at": "2026-01-24T00:00:00Z",
        }
    ]

    service.insert_chunks(records)

    assert client.calls
    assert "INSERT INTO chunks" in client.calls[0][0]
