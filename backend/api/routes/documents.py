from fastapi import APIRouter, HTTPException, status

from backend.core.logging import log_handler
from backend.models.schemas import DocumentUploadRequest, DocumentUploadResponse
from backend.services.tower_service import TowerService

router = APIRouter()
tower_service = TowerService()


@router.post("/documents", response_model=DocumentUploadResponse)
async def upload_document(payload: DocumentUploadRequest) -> DocumentUploadResponse:
    """
    Upload a document to Tower.
    
    This endpoint accepts a PDF URL or file and processes it through
    the document-ingestion Tower app.
    
    Args:
        payload: Document upload request with company_id and optional pdf_url
        
    Returns:
        DocumentUploadResponse with document_id and status
    """
    log_handler.info(f"Received document upload request for company: {payload.company_id}")
    
    if not payload.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="company_id is required"
        )
    
    if not payload.pdf_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="pdf_url is required (file upload not yet supported)"
        )
    
    try:
        # Call document-ingestion Tower app
        result = tower_service.call_document_ingestion(
            pdf_url=payload.pdf_url,
            company_id=payload.company_id,
            version="v1",  # Default version, could be parameterized
            source_url=payload.pdf_url
        )
        
        document = result.get("document", {})
        document_id = document.get("document_id", "unknown")
        
        log_handler.info(f"Document uploaded successfully: {document_id}")
        
        return DocumentUploadResponse(
            document_id=document_id,
            status="completed"
        )
        
    except Exception as e:
        error_msg = f"Error uploading document: {str(e)}"
        log_handler.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
