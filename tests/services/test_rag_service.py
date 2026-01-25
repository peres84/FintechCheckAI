"""
Tests for RAG Service.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from backend.services.rag_service import (
    retrieve_chunks_simple,
    retrieve_chunks_semantic,
    retrieve_chunks_hybrid,
    retrieve_chunks_from_tower,
    _cosine_similarity,
    _tokenize,
)


class TestRAGServiceHelpers:
    """Test helper functions."""

    def test_tokenize(self):
        """Test text tokenization."""
        text = "Hello World 123"
        tokens = _tokenize(text)
        assert "hello" in tokens
        assert "world" in tokens
        assert "123" in tokens
        assert len(tokens) == 3

    def test_cosine_similarity_identical(self):
        """Test cosine similarity with identical vectors."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = _cosine_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 0.001

    def test_cosine_similarity_orthogonal(self):
        """Test cosine similarity with orthogonal vectors."""
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]
        similarity = _cosine_similarity(vec1, vec2)
        assert abs(similarity - 0.0) < 0.001

    def test_cosine_similarity_empty(self):
        """Test cosine similarity with empty vectors."""
        similarity = _cosine_similarity([], [])
        assert similarity == 0.0

    def test_cosine_similarity_different_lengths(self):
        """Test cosine similarity with different length vectors."""
        vec1 = [1.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = _cosine_similarity(vec1, vec2)
        # Should use minimum length
        assert similarity > 0.0


class TestRAGServiceKeyword:
    """Test keyword-based retrieval."""

    def test_retrieve_chunks_simple(self):
        """Test simple keyword retrieval."""
        query = "revenue growth"
        chunks = [
            {"content": "Our revenue grew by 25%", "chunk_id": "1"},
            {"content": "User engagement increased", "chunk_id": "2"},
            {"content": "Revenue growth was strong", "chunk_id": "3"},
        ]
        
        results = retrieve_chunks_simple(query, chunks, top_k=2)
        
        assert len(results) == 2
        assert results[0]["chunk_id"] == "3"  # "revenue growth" matches best
        assert "score" in results[0]

    def test_retrieve_chunks_simple_no_matches(self):
        """Test keyword retrieval with no matches."""
        query = "xyz abc"
        chunks = [
            {"content": "Our revenue grew", "chunk_id": "1"},
        ]
        
        results = retrieve_chunks_simple(query, chunks, top_k=5)
        
        assert len(results) == 1
        assert results[0]["score"] == 0.0

    def test_retrieve_chunks_simple_empty_chunks(self):
        """Test keyword retrieval with empty chunks."""
        query = "test"
        results = retrieve_chunks_simple(query, [], top_k=5)
        assert len(results) == 0


class TestRAGServiceSemantic:
    """Test semantic search."""

    def test_retrieve_chunks_semantic(self):
        """Test semantic retrieval with embeddings."""
        query_embedding = [0.1, 0.2, 0.3, 0.4]
        chunks = [
            {
                "content": "Revenue information",
                "chunk_id": "1",
                "embedding": [0.1, 0.2, 0.3, 0.4]  # Same as query
            },
            {
                "content": "User metrics",
                "chunk_id": "2",
                "embedding": [0.9, 0.8, 0.7, 0.6]  # Different
            },
            {
                "content": "Financial data",
                "chunk_id": "3",
                "embedding": [0.15, 0.25, 0.35, 0.45]  # Similar
            },
        ]
        
        results = retrieve_chunks_semantic(query_embedding, chunks, top_k=2)
        
        assert len(results) == 2
        assert results[0]["chunk_id"] == "1"  # Most similar
        assert "score" in results[0]
        assert "similarity" in results[0]

    def test_retrieve_chunks_semantic_no_embeddings(self):
        """Test semantic retrieval with chunks without embeddings."""
        query_embedding = [0.1, 0.2, 0.3]
        chunks = [
            {"content": "Test", "chunk_id": "1"},  # No embedding
            {"content": "Test 2", "chunk_id": "2", "embedding": []},  # Empty embedding
        ]
        
        results = retrieve_chunks_semantic(query_embedding, chunks, top_k=5)
        
        # Should skip chunks without valid embeddings
        assert len(results) == 0

    def test_retrieve_chunks_semantic_empty_query(self):
        """Test semantic retrieval with empty query embedding."""
        results = retrieve_chunks_semantic([], [{"content": "Test", "embedding": [0.1, 0.2]}], top_k=5)
        assert len(results) == 0


class TestRAGServiceHybrid:
    """Test hybrid search."""

    def test_retrieve_chunks_hybrid(self):
        """Test hybrid search combining semantic and keyword."""
        query = "revenue growth"
        query_embedding = [0.1, 0.2, 0.3]
        chunks = [
            {
                "content": "Revenue growth was strong",
                "chunk_id": "1",
                "embedding": [0.1, 0.2, 0.3]  # Good semantic match
            },
            {
                "content": "User engagement increased",
                "chunk_id": "2",
                "embedding": [0.9, 0.8, 0.7]  # Poor semantic match
            },
        ]
        
        results = retrieve_chunks_hybrid(
            query,
            query_embedding,
            chunks,
            top_k=2,
            semantic_weight=0.7,
            keyword_weight=0.3
        )
        
        assert len(results) == 2
        assert "score" in results[0]
        assert "semantic_score" in results[0]
        assert "keyword_score" in results[0]
        # First chunk should score higher (good semantic + keyword match)
        assert results[0]["chunk_id"] == "1"

    def test_retrieve_chunks_hybrid_no_embedding(self):
        """Test hybrid search without query embedding (keyword only)."""
        query = "revenue"
        chunks = [
            {"content": "Revenue was high", "chunk_id": "1"},
            {"content": "Users increased", "chunk_id": "2"},
        ]
        
        results = retrieve_chunks_hybrid(query, None, chunks, top_k=2)
        
        # Should still work with keyword matching
        assert len(results) == 2
        assert results[0]["chunk_id"] == "1"

    def test_retrieve_chunks_hybrid_weight_normalization(self):
        """Test that weights are normalized correctly."""
        query = "test"
        query_embedding = [0.1, 0.2]
        chunks = [{"content": "test", "chunk_id": "1", "embedding": [0.1, 0.2]}]
        
        # Weights that don't sum to 1 should be normalized
        results = retrieve_chunks_hybrid(
            query,
            query_embedding,
            chunks,
            top_k=1,
            semantic_weight=0.8,
            keyword_weight=0.4  # Total > 1
        )
        
        assert len(results) == 1
        assert results[0]["score"] <= 1.0


class TestRAGServiceTower:
    """Test Tower integration."""

    @pytest.mark.asyncio
    @patch("backend.services.rag_service.TOWER_RAG_AVAILABLE", True)
    @patch("backend.services.rag_service.TowerChunkStore")
    @patch("backend.services.rag_service._get_query_embedding")
    async def test_retrieve_chunks_from_tower_keyword(self, mock_embedding, mock_store_class):
        """Test Tower retrieval with keyword search."""
        # Mock chunk store
        mock_store = Mock()
        mock_store.read_all.return_value = [
            {"document_id": "doc1", "content": "Revenue grew", "chunk_id": "1"},
            {"document_id": "doc2", "content": "Users increased", "chunk_id": "2"},
        ]
        mock_store_class.return_value = mock_store
        
        results = await retrieve_chunks_from_tower(
            document_id="doc1",
            query="revenue",
            top_k=1,
            search_method="keyword"
        )
        
        assert len(results) == 1
        assert results[0]["chunk_id"] == "1"
        mock_embedding.assert_not_called()  # Should not generate embedding for keyword search

    @pytest.mark.asyncio
    @patch("backend.services.rag_service.TOWER_RAG_AVAILABLE", True)
    @patch("backend.services.rag_service.TowerChunkStore")
    @patch("backend.services.rag_service._get_query_embedding")
    async def test_retrieve_chunks_from_tower_semantic(self, mock_embedding, mock_store_class):
        """Test Tower retrieval with semantic search."""
        # Mock embedding
        mock_embedding.return_value = [0.1, 0.2, 0.3]
        
        # Mock chunk store
        mock_store = Mock()
        mock_store.read_all.return_value = [
            {
                "document_id": "doc1",
                "content": "Revenue",
                "chunk_id": "1",
                "embedding": [0.1, 0.2, 0.3]
            },
        ]
        mock_store_class.return_value = mock_store
        
        results = await retrieve_chunks_from_tower(
            document_id="doc1",
            query="revenue",
            top_k=1,
            search_method="semantic"
        )
        
        assert len(results) == 1
        mock_embedding.assert_called_once()

    @pytest.mark.asyncio
    @patch("backend.services.rag_service.TOWER_RAG_AVAILABLE", False)
    async def test_retrieve_chunks_from_tower_unavailable(self):
        """Test Tower retrieval when Tower is unavailable."""
        results = await retrieve_chunks_from_tower(
            document_id="doc1",
            query="test",
            top_k=5
        )
        
        assert len(results) == 0

    @pytest.mark.asyncio
    @patch("backend.services.rag_service.TOWER_RAG_AVAILABLE", True)
    @patch("backend.services.rag_service.TowerChunkStore")
    @patch("backend.services.rag_service._get_query_embedding")
    async def test_retrieve_chunks_from_tower_hybrid_fallback(self, mock_embedding, mock_store_class):
        """Test hybrid search falling back to keyword when embedding fails."""
        # Mock embedding to return None
        mock_embedding.return_value = None
        
        # Mock chunk store
        mock_store = Mock()
        mock_store.read_all.return_value = [
            {"document_id": "doc1", "content": "Revenue grew", "chunk_id": "1"},
        ]
        mock_store_class.return_value = mock_store
        
        results = await retrieve_chunks_from_tower(
            document_id="doc1",
            query="revenue",
            top_k=1,
            search_method="hybrid"
        )
        
        # Should fall back to keyword search
        assert len(results) == 1
        mock_embedding.assert_called_once()
