import pytest
import os
import sys
from unittest.mock import patch, AsyncMock, MagicMock
from io import BytesIO

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from fastapi.testclient import TestClient
from fastapi import status
from backend.main import app


class TestAIAgentAPI:
    """Test cases for AI Agent API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_transcript(self):
        """Sample transcript text."""
        return """
        Our revenue grew by 25% this quarter, reaching $100 million in total revenue.
        We saw a 15% increase in user engagement and our profit margins improved to 18%.
        Looking ahead, we expect continued growth of 20% next quarter.
        """
    
    @pytest.fixture
    def sample_shareholder_letter(self):
        """Sample shareholder letter text."""
        return """
        Dear Shareholders,
        
        I'm pleased to report that our Q3 results exceeded expectations.
        Revenue increased by 23% compared to the previous quarter, reaching $98 million.
        Our user engagement metrics showed strong improvement with a 16% increase.
        
        Best regards,
        CEO
        """
    
    @pytest.fixture
    def sample_claims(self):
        """Sample extracted claims."""
        return [
            {
                "claim": "Revenue grew by 25% this quarter",
                "category": "revenue",
                "confidence": "high",
                "numerical_values": ["25%"],
                "context": "quarterly financial performance"
            }
        ]
    
    def test_health_endpoint(self, client):
        """Test AI agent health check endpoint."""
        response = client.get("/api/ai-agent/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "AI Agent Service"
        assert "endpoints" in data
        assert "ai_model" in data
    
    @pytest.mark.asyncio
    @patch('backend.api.routes.ai_agent.ai_agent_service')
    async def test_extract_claims_endpoint(self, mock_service, client, sample_transcript):
        """Test extract claims endpoint."""
        # Mock the service response
        mock_claims = [
            {
                "claim": "Revenue grew by 25% this quarter",
                "category": "revenue",
                "confidence": "high",
                "numerical_values": ["25%"],
                "context": "quarterly performance"
            }
        ]
        mock_service.extract_claims_from_transcript = AsyncMock(return_value=mock_claims)
        
        # Make request
        response = client.post(
            "/api/ai-agent/extract-claims",
            json={"transcript": sample_transcript}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "claims" in data
        assert "total_claims" in data
        assert "categories" in data
        assert data["total_claims"] == 1
    
    def test_extract_claims_empty_transcript(self, client):
        """Test extract claims with empty transcript."""
        response = client.post(
            "/api/ai-agent/extract-claims",
            json={"transcript": ""}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.asyncio
    @patch('backend.api.routes.ai_agent.ai_agent_service')
    async def test_compare_claims_endpoint(self, mock_service, client, sample_claims, sample_shareholder_letter):
        """Test compare claims endpoint."""
        # Mock the service response
        mock_comparison = {
            "verified_claims": [
                {
                    "claim": "Revenue grew by 25% this quarter",
                    "status": "CONTRADICTED",
                    "evidence": "Revenue increased by 23%",
                    "confidence": "high"
                }
            ],
            "summary": {
                "total_claims": 1,
                "verified": 0,
                "contradicted": 1,
                "not_found": 0
            },
            "key_discrepancies": []
        }
        mock_service.compare_with_shareholder_letter = AsyncMock(return_value=mock_comparison)
        
        # Make request
        response = client.post(
            "/api/ai-agent/compare-claims",
            json={
                "claims": sample_claims,
                "shareholder_letter": sample_shareholder_letter
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "verified_claims" in data
        assert "summary" in data
        assert "key_discrepancies" in data
    
    def test_compare_claims_empty_claims(self, client, sample_shareholder_letter):
        """Test compare claims with empty claims."""
        response = client.post(
            "/api/ai-agent/compare-claims",
            json={
                "claims": [],
                "shareholder_letter": sample_shareholder_letter
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_compare_claims_empty_letter(self, client, sample_claims):
        """Test compare claims with empty shareholder letter."""
        response = client.post(
            "/api/ai-agent/compare-claims",
            json={
                "claims": sample_claims,
                "shareholder_letter": ""
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.asyncio
    @patch('backend.api.routes.ai_agent.fetch_transcript')
    @patch('backend.api.routes.ai_agent.ai_agent_service')
    async def test_verify_youtube_video_endpoint(
        self, 
        mock_service, 
        mock_fetch_transcript,
        client, 
        sample_transcript
    ):
        """Test verify YouTube video endpoint."""
        # Mock transcript fetch
        mock_fetch_transcript.return_value = {
            "transcript": sample_transcript,
            "video_id": "test_video_id",
            "source": "youtube_captions",
            "status": "completed"
        }
        
        # Mock service methods
        mock_claims = [{"claim": "Test claim", "category": "revenue"}]
        mock_service.extract_claims_from_transcript = AsyncMock(return_value=mock_claims)
        mock_service.compare_with_shareholder_letter = AsyncMock(return_value={
            "verified_claims": [],
            "summary": {"total_claims": 1},
            "key_discrepancies": []
        })
        mock_service.generate_verification_report = AsyncMock(return_value={
            "executive_summary": "Test summary",
            "recommendations": ["Test recommendation"],
            "metadata": {"test": "data"}
        })
        
        # Make request
        response = client.post(
            "/api/ai-agent/verify-youtube-video",
            json={
                "youtube_url": "https://www.youtube.com/watch?v=test",
                "shareholder_letter": None
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "video_id" in data
        assert "transcript" in data
        assert "extracted_claims" in data
        assert "verification_results" in data
    
    @pytest.mark.asyncio
    @patch('backend.api.routes.ai_agent.ai_agent_service')
    async def test_verify_from_files_endpoint(
        self,
        mock_service,
        client,
        sample_transcript,
        sample_shareholder_letter
    ):
        """Test verify from files endpoint."""
        # Mock service methods
        mock_claims = [{"claim": "Test claim", "category": "revenue"}]
        mock_service.extract_claims_from_transcript = AsyncMock(return_value=mock_claims)
        mock_service.compare_with_shareholder_letter = AsyncMock(return_value={
            "verified_claims": [],
            "summary": {"total_claims": 1},
            "key_discrepancies": []
        })
        mock_service.generate_verification_report = AsyncMock(return_value={
            "executive_summary": "Test summary",
            "recommendations": ["Test recommendation"],
            "metadata": {"test": "data"}
        })
        
        # Create file-like objects
        transcript_file = ("transcript.txt", BytesIO(sample_transcript.encode('utf-8')), "text/plain")
        shareholder_file = ("letter.txt", BytesIO(sample_shareholder_letter.encode('utf-8')), "text/plain")
        
        # Make request
        response = client.post(
            "/api/ai-agent/verify-from-files",
            files={
                "transcript_file": transcript_file,
                "shareholder_letter_file": shareholder_file
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "transcript" in data
        assert "extracted_claims" in data
        assert "verification_results" in data
    
    @pytest.mark.asyncio
    @patch('backend.api.routes.ai_agent.ai_agent_service')
    async def test_verify_from_files_transcript_only(
        self,
        mock_service,
        client,
        sample_transcript
    ):
        """Test verify from files endpoint with only transcript."""
        # Mock service methods
        mock_claims = [{"claim": "Test claim", "category": "revenue"}]
        mock_service.extract_claims_from_transcript = AsyncMock(return_value=mock_claims)
        mock_service.generate_verification_report = AsyncMock(return_value={
            "executive_summary": "Test summary",
            "recommendations": ["Test recommendation"],
            "metadata": {"test": "data"}
        })
        
        # Create file-like object
        transcript_file = ("transcript.txt", BytesIO(sample_transcript.encode('utf-8')), "text/plain")
        
        # Make request
        response = client.post(
            "/api/ai-agent/verify-from-files",
            files={
                "transcript_file": transcript_file
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "transcript" in data
        assert "extracted_claims" in data
    
    def test_verify_from_files_invalid_file_type(self, client, sample_transcript):
        """Test verify from files with invalid file type."""
        # Create file-like object with wrong extension
        transcript_file = ("transcript.pdf", BytesIO(sample_transcript.encode('utf-8')), "application/pdf")
        
        # Make request
        response = client.post(
            "/api/ai-agent/verify-from-files",
            files={
                "transcript_file": transcript_file
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_verify_from_files_empty_file(self, client):
        """Test verify from files with empty file."""
        # Create empty file-like object
        transcript_file = ("transcript.txt", BytesIO(b""), "text/plain")
        
        # Make request
        response = client.post(
            "/api/ai-agent/verify-from-files",
            files={
                "transcript_file": transcript_file
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
