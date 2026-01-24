from typing import Any, List

from pydantic import BaseModel


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
