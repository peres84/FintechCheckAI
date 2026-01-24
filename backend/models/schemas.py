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
