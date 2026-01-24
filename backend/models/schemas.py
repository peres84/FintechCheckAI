from typing import Any, List, Optional

from pydantic import BaseModel, HttpUrl


class VerificationRequest(BaseModel):
    youtube_url: str
    company_id: str


class VerificationResponse(BaseModel):
    results: List[dict[str, Any]]


class DocumentUploadRequest(BaseModel):
    company_id: str
    pdf_url: str | None = None


class DocumentUploadResponse(BaseModel):
    document_id: str
    status: str


# YouTube service models
class YouTubeTranscriptRequest(BaseModel):
    url: HttpUrl
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            }
        }


class YouTubeTranscriptResponse(BaseModel):
    video_id: str
    video_url: str
    transcript: str
    source: str  # "youtube_captions" or "audio_transcription"
    status: str  # "completed", "failed", "processing"
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "dQw4w9WgXcQ",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "transcript": "Never gonna give you up, never gonna let you down...",
                "source": "youtube_captions",
                "status": "completed",
                "error": None
            }
        }


# AI Agent service models
class ClaimExtractionRequest(BaseModel):
    transcript: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "transcript": "Our revenue grew by 25% this quarter, reaching $100 million..."
            }
        }


class ClaimExtractionResponse(BaseModel):
    claims: List[dict[str, Any]]
    total_claims: int
    categories: dict[str, int]
    
    class Config:
        json_schema_extra = {
            "example": {
                "claims": [
                    {
                        "claim": "Revenue grew by 25% this quarter",
                        "category": "revenue",
                        "confidence": "high",
                        "numerical_values": ["25%"],
                        "context": "quarterly financial performance"
                    }
                ],
                "total_claims": 1,
                "categories": {"revenue": 1}
            }
        }


class VerificationAnalysisRequest(BaseModel):
    youtube_url: HttpUrl
    shareholder_letter: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "shareholder_letter": "Dear shareholders, our Q3 results show..."
            }
        }


class VerificationAnalysisResponse(BaseModel):
    video_id: str
    video_url: str
    transcript: str
    extracted_claims: List[dict[str, Any]]
    verification_results: dict[str, Any]
    executive_summary: str
    recommendations: List[str]
    metadata: dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "dQw4w9WgXcQ",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "transcript": "Our revenue grew by 25%...",
                "extracted_claims": [],
                "verification_results": {},
                "executive_summary": "Analysis complete",
                "recommendations": ["Review claims"],
                "metadata": {"analysis_timestamp": "2024-01-24T20:00:00"}
            }
        }


class ComparisonRequest(BaseModel):
    claims: List[dict[str, Any]]
    shareholder_letter: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "claims": [
                    {
                        "claim": "Revenue grew by 25%",
                        "category": "revenue",
                        "confidence": "high"
                    }
                ],
                "shareholder_letter": "Dear shareholders, our revenue increased by 23%..."
            }
        }


class ComparisonResponse(BaseModel):
    verified_claims: List[dict[str, Any]]
    summary: dict[str, Any]
    key_discrepancies: List[dict[str, Any]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "verified_claims": [],
                "summary": {"total_claims": 1, "verified": 0, "contradicted": 1},
                "key_discrepancies": []
            }
        }
