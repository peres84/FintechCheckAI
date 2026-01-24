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


# Company listing models
class Company(BaseModel):
    company_id: str
    name: str
    ticker: Optional[str] = None
    industry: Optional[str] = None
    created_at: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "duolingo",
                "name": "Duolingo",
                "ticker": "DUOL",
                "industry": "Education Technology",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


class CompanyListResponse(BaseModel):
    companies: List[Company]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "companies": [
                    {
                        "company_id": "duolingo",
                        "name": "Duolingo",
                        "ticker": "DUOL"
                    }
                ],
                "total": 1
            }
        }


# Version diff models
class VersionDiffRequest(BaseModel):
    company_id: str
    document_id_1: str
    document_id_2: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "duolingo",
                "document_id_1": "doc_2024_q3",
                "document_id_2": "doc_2024_q2"
            }
        }


class DocumentVersion(BaseModel):
    document_id: str
    version: str
    sha256: str
    created_at: str
    page_count: Optional[int] = None


class ChangedSection(BaseModel):
    section: str
    page: int
    old_text: str
    new_text: str
    change_type: str  # "added", "removed", "modified"


class VersionDiffResponse(BaseModel):
    company_id: str
    document_1: DocumentVersion
    document_2: DocumentVersion
    changed_sections: List[ChangedSection]
    total_changes: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "duolingo",
                "document_1": {
                    "document_id": "doc_2024_q3",
                    "version": "Q3-2024",
                    "sha256": "abc123...",
                    "created_at": "2024-09-30T00:00:00Z"
                },
                "document_2": {
                    "document_id": "doc_2024_q2",
                    "version": "Q2-2024",
                    "sha256": "def456...",
                    "created_at": "2024-06-30T00:00:00Z"
                },
                "changed_sections": [],
                "total_changes": 0
            }
        }
