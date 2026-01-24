import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from typing import Dict, Any

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.services.opik_service import OpikService, get_opik_service, OPIK_AVAILABLE


class TestOpikService:
    """Test cases for Opik Service."""
    
    @pytest.fixture
    def service(self):
        """Create Opik Service instance for testing."""
        # Reset global instance
        import backend.services.opik_service as opik_module
        opik_module._opik_service_instance = None
        return OpikService()
    
    def test_service_initialization_without_opik(self, service):
        """Test service initializes even if Opik SDK not available."""
        # Service should initialize without errors
        assert service is not None
        assert hasattr(service, 'client')
        assert hasattr(service, 'enabled')
    
    @pytest.mark.skipif(not OPIK_AVAILABLE, reason="Opik SDK not installed")
    @patch.dict(os.environ, {}, clear=True)
    def test_service_initialization_no_api_key(self, service):
        """Test service initializes in no-op mode without API key."""
        assert service is not None
        # Should be disabled if no API key
        assert not service.is_enabled()
    
    def test_track_claim_extraction(self, service):
        """Test claim extraction tracking."""
        transcript = "Duolingo reported $150M revenue this quarter."
        claims = [
            {
                "claim": "Revenue: $150M",
                "category": "revenue",
                "confidence": "high"
            }
        ]
        
        result = service.track_claim_extraction(transcript, claims)
        
        assert "input" in result
        assert "output" in result
        assert result["input"]["transcript_length"] == len(transcript)
        assert result["output"]["claims_count"] == 1
        assert result["output"]["claims"] == claims
    
    def test_track_claim_extraction_empty(self, service):
        """Test claim extraction tracking with empty claims."""
        transcript = "No claims here."
        claims = []
        
        result = service.track_claim_extraction(transcript, claims)
        
        assert result["output"]["claims_count"] == 0
        assert result["output"]["claims"] == []
    
    def test_track_claim_extraction_with_metadata(self, service):
        """Test claim extraction tracking with metadata."""
        transcript = "Test transcript"
        claims = [{"claim": "Test"}]
        metadata = {"video_id": "test123", "timestamp": "2024-01-01"}
        
        result = service.track_claim_extraction(transcript, claims, metadata)
        
        assert "metadata" in result
        assert result["metadata"] == metadata
    
    def test_track_chunk_retrieval(self, service):
        """Test chunk retrieval tracking."""
        query = "revenue Q3 2024"
        chunks = ["chunk1", "chunk2"]
        scores = [0.9, 0.8]
        
        result = service.track_chunk_retrieval(query, chunks, scores)
        
        assert "input" in result
        assert "output" in result
        assert result["input"]["query"] == query
        assert result["output"]["chunks_count"] == 2
        assert result["output"]["avg_score"] == 0.85
        assert result["output"]["chunks"] == chunks
    
    def test_track_chunk_retrieval_empty(self, service):
        """Test chunk retrieval tracking with empty results."""
        query = "test query"
        chunks = []
        scores = []
        
        result = service.track_chunk_retrieval(query, chunks, scores)
        
        assert result["output"]["chunks_count"] == 0
        assert result["output"]["avg_score"] == 0.0
    
    def test_track_verification(self, service):
        """Test verification tracking."""
        claim = "Revenue was $150M"
        chunks = ["context chunk about revenue"]
        verdict = "VERIFIED"
        reasoning = "Found in Q3 report, page 5"
        
        result = service.track_verification(claim, chunks, verdict, reasoning)
        
        assert "input" in result
        assert "context" in result
        assert "output" in result
        assert result["input"]["claim"] == claim
        assert result["context"]["chunks"] == chunks
        assert result["output"]["verdict"] == verdict
        assert result["output"]["reasoning"] == reasoning
    
    def test_track_llm_call(self, service):
        """Test LLM call tracking."""
        model = "gpt-4o-mini"
        prompt = "Extract claims from this transcript..."
        response = "Here are the claims..."
        tokens_used = 150
        
        result = service.track_llm_call(model, prompt, response, tokens_used)
        
        assert result["model"] == model
        assert "input" in result
        assert "output" in result
        assert result["tokens_used"] == tokens_used
        assert result["input"]["prompt_length"] == len(prompt)
        assert result["output"]["response_length"] == len(response)
    
    def test_track_llm_call_no_tokens(self, service):
        """Test LLM call tracking without token count."""
        model = "gpt-4o-mini"
        prompt = "Test prompt"
        response = "Test response"
        
        result = service.track_llm_call(model, prompt, response)
        
        assert result["model"] == model
        assert "tokens_used" not in result
    
    def test_log_error(self, service):
        """Test error logging."""
        operation = "claim_extraction"
        error = ValueError("Test error")
        context = {"video_id": "test123"}
        
        # Should not raise
        service.log_error(operation, error, context)
        
        # Just verify it doesn't crash
        assert True
    
    def test_is_enabled(self, service):
        """Test is_enabled method."""
        # Service may or may not be enabled depending on environment
        enabled = service.is_enabled()
        assert isinstance(enabled, bool)
    
    def test_get_opik_service_singleton(self):
        """Test that get_opik_service returns singleton."""
        import backend.services.opik_service as opik_module
        opik_module._opik_service_instance = None
        
        service1 = get_opik_service()
        service2 = get_opik_service()
        
        # Should be the same instance
        assert service1 is service2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
