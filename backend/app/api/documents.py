from fastapi import APIRouter

from ..models.schemas import DocumentUploadRequest, DocumentUploadResponse

router = APIRouter()


@router.post("/documents", response_model=DocumentUploadResponse)
def upload_document(payload: DocumentUploadRequest) -> DocumentUploadResponse:
    return DocumentUploadResponse(document_id="pending", status="not_implemented")
