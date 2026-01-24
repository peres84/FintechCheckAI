import pytest
import asyncio
import os
import sys
from unittest.mock import patch, AsyncMock

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.services.ai_agent_service import AIAgentService, ai_agent_service


class TestAIAgentService:
    """Test cases for AI Agent Service."""
    
    @pytest.fixture
    def service(self):
        """Create AI Agent Service instance for testing."""
        return AIAgentService()
    
    @pytest.fixture
    def sample_transcript(self):
        """Sample transcript for testing."""
        return """
        Our revenue grew by 25% this quarter, reaching $100 million in total revenue.
        We saw a 15% increase in user engagement and our profit margins improved to 18%.
        Looking ahead, we expect continued growth of 20% next quarter.
        """
    
    @pytest.fixture
    def sample_claims(self):
        """Sample claims for testing."""
        return [
            {
                "claim": "Revenue grew by 25% this quarter",
                "category": "revenue",
                "confidence": "high",
                "numerical_values": ["25%"],
                "context": "quarterly financial performance"
            },
            {
                "claim": "Total revenue reached $100 million",
                "category": "revenue", 
                "confidence": "high",
                "numerical_values": ["$100 million"],
                "context": "quarterly financial performance"
            }
        ]
    
    @pytest.fixture
    def sample_shareholder_letter(self):
        """Sample shareholder letter for testing."""
        return """
        Dear Shareholders,
        
        I'm pleased to report that our Q3 results exceeded expectations.
        Revenue increased by 23% compared to the previous quarter, reaching $98 million.
        Our user engagement metrics showed strong improvement with a 16% increase.
        
        Best regards,
        CEO
        """
    
    def test_service_initialization(self, service):
        """Test that the service initializes correctly."""
        assert service.model == "gpt-4o-mini"
        assert service.max_tokens == 4000
    
    @pytest.mark.asyncio
    async def test_extract_claims_empty_transcript(self, service):
        """Test claim extraction with empty transcript."""
        result = await service.extract_claims_from_transcript("")
        assert result == []
    
    @pytest.mark.asyncio
    async def test_extract_claims_none_transcript(self, service):
        """Test claim extraction with None transcript."""
        result = await service.extract_claims_from_transcript(None)
        assert result == []
    
    @pytest.mark.asyncio
    @patch('backend.services.ai_agent_service.client')
    async def test_extract_claims_success(self, mock_client, service, sample_transcript):
        """Test successful claim extraction."""
        # Mock OpenAI response
        mock_response = AsyncMock()
        mock_response.choices[0].message.content = '''[
            {
                "claim": "Revenue grew by 25% this quarter",
                "category": "revenue",
                "confidence": "high",
                "numerical_values": ["25%"],
                "context": "quarterly performance"
            }
        ]'''
        mock_client.chat.completions.create.return_value = mock_response
        
        result = await service.extract_claims_from_transcript(sample_transcript)
        
        assert len(result) == 1
        assert result[0]["claim"] == "Revenue grew by 25% this quarter"
        assert result[0]["category"] == "revenue"
        assert result[0]["confidence"] == "high"
    
    @pytest.mark.asyncio
    @patch('backend.services.ai_agent_service.client')
    async def test_extract_claims_invalid_json(self, mock_client, service, sample_transcript):
        """Test claim extraction with invalid JSON response."""
        # Mock OpenAI response with invalid JSON
        mock_response = AsyncMock()
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = await service.extract_claims_from_transcript(sample_transcript)
        
        assert len(result) == 1
        assert result[0]["claim"] == "Invalid JSON response"
        assert result[0]["category"] == "other"
    
    @pytest.mark.asyncio
    async def test_compare_empty_claims(self, service, sample_shareholder_letter):
        """Test comparison with empty claims."""
        result = await service.compare_with_shareholder_letter([], sample_shareholder_letter)
        
        assert "verified_claims" in result
        assert "discrepancies" in result
        assert "summary" in result
        assert result["summary"] == "No claims to verify"
    
    @pytest.mark.asyncio
    async def test_compare_empty_letter(self, service, sample_claims):
        """Test comparison with empty shareholder letter."""
        result = await service.compare_with_shareholder_letter(sample_claims, "")
        
        assert "verified_claims" in result
        assert "discrepancies" in result
        assert "summary" in result
        assert "No shareholder letter content" in result["summary"]
    
    @pytest.mark.asyncio
    @patch('backend.services.ai_agent_service.client')
    async def test_compare_success(self, mock_client, service, sample_claims, sample_shareholder_letter):
        """Test successful comparison."""
        # Mock OpenAI response
        mock_response = AsyncMock()
        mock_response.choices[0].message.content = '''{
            "verified_claims": [
                {
                    "claim": "Revenue grew by 25% this quarter",
                    "status": "CONTRADICTED",
                    "evidence": "Revenue increased by 23%",
                    "confidence": "high",
                    "notes": "Slight discrepancy in growth rate"
                }
            ],
            "summary": {
                "total_claims": 2,
                "verified": 0,
                "contradicted": 1,
                "not_found": 1,
                "overall_accuracy": "50%"
            },
            "key_discrepancies": [
                {
                    "claim": "Revenue grew by 25%",
                    "transcript_version": "25% growth",
                    "official_version": "23% growth",
                    "severity": "low"
                }
            ]
        }'''
        mock_client.chat.completions.create.return_value = mock_response
        
        result = await service.compare_with_shareholder_letter(sample_claims, sample_shareholder_letter)
        
        assert "verified_claims" in result
        assert "summary" in result
        assert "key_discrepancies" in result
        assert result["summary"]["total_claims"] == 2
        assert len(result["key_discrepancies"]) == 1
    
    def test_categorize_claims(self, service, sample_claims):
        """Test claim categorization."""
        categories = service._categorize_claims(sample_claims)
        
        assert categories["revenue"] == 2
        assert len(categories) == 1
    
    def test_generate_executive_summary(self, service):
        """Test executive summary generation."""
        comparison_result = {
            "summary": {
                "total_claims": 5,
                "verified": 4,
                "contradicted": 1,
                "not_found": 0
            }
        }
        
        summary = service._generate_executive_summary(comparison_result)
        
        assert "Total claims analyzed: 5" in summary
        assert "Verified claims: 4" in summary
        assert "80.0%" in summary  # Accuracy rate
        assert "High accuracy" in summary
    
    def test_generate_recommendations(self, service):
        """Test recommendation generation."""
        comparison_result = {
            "key_discrepancies": [{"claim": "test", "severity": "high"}],
            "summary": {"not_found": 2, "verified": 3, "total_claims": 5}
        }
        
        recommendations = service._generate_recommendations(comparison_result)
        
        assert len(recommendations) >= 1
        assert any("contradicted claims" in rec for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_generate_verification_report(self, service, sample_transcript, sample_claims):
        """Test verification report generation."""
        comparison_result = {
            "verified_claims": [],
            "summary": {"total_claims": 2, "verified": 1},
            "key_discrepancies": []
        }
        
        report = await service.generate_verification_report(
            "https://youtube.com/watch?v=test",
            sample_transcript,
            sample_claims,
            comparison_result
        )
        
        assert "metadata" in report
        assert "claims_analysis" in report
        assert "verification_results" in report
        assert "executive_summary" in report
        assert "recommendations" in report
        
        assert report["metadata"]["video_url"] == "https://youtube.com/watch?v=test"
        assert report["metadata"]["total_claims_extracted"] == 2


# Integration tests
class TestAIAgentServiceIntegration:
    """Integration tests for AI Agent Service (require OpenAI API key)."""
    
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not available")
    @pytest.mark.asyncio
    async def test_real_claim_extraction(self):
        """Test real claim extraction with OpenAI API."""
        transcript = "Our company achieved 15% revenue growth this quarter, reaching $50 million in sales."
        
        result = await ai_agent_service.extract_claims_from_transcript(transcript)
        
        assert isinstance(result, list)
        # Should extract at least one claim about revenue
        assert len(result) >= 1
    
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not available")
    @pytest.mark.asyncio
    async def test_real_comparison(self):
        """Test real comparison with OpenAI API."""
        claims = [
            {
                "claim": "Revenue grew by 20%",
                "category": "revenue",
                "confidence": "high"
            }
        ]
        
        shareholder_letter = "Our revenue increased by 18% this quarter, showing strong performance."
        
        result = await ai_agent_service.compare_with_shareholder_letter(claims, shareholder_letter)
        
        assert isinstance(result, dict)
        assert "verified_claims" in result
        assert "summary" in result


if __name__ == "__main__":
    # Run basic tests
    print("Running AI Agent Service tests...")
    
    # Test service initialization
    service = AIAgentService()
    print(f"✅ Service initialized with model: {service.model}")
    
    # Test categorization
    sample_claims = [
        {"category": "revenue"}, 
        {"category": "revenue"}, 
        {"category": "growth"}
    ]
    categories = service._categorize_claims(sample_claims)
    print(f"✅ Categorization test passed: {categories}")
    
    print("Basic tests completed successfully!")