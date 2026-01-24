from backend.services.rag_service import retrieve_chunks


def test_retrieve_chunks_scores_overlap():
    chunks = [
        {"content": "Duolingo reported revenue growth"},
        {"content": "User engagement increased"},
    ]

    result = retrieve_chunks("revenue growth", chunks, top_k=1)

    assert result
    assert result[0]["content"] == "Duolingo reported revenue growth"
