import base64
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from backend.core.logging import log_handler
from backend.models.schemas import DocumentUploadRequest, DocumentUploadResponse
from backend.services.pdf_service import pdf_service
from backend.services.tower_service import TowerService

router = APIRouter()


def get_tower_service() -> TowerService:
    """Get Tower service instance (lazy initialization)."""
    try:
        return TowerService()
    except RuntimeError as e:
        log_handler.warning(f"Tower service unavailable: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document storage service is currently unavailable"
        )

# ImageKit configuration
IMAGEKIT_UPLOAD_URL = "https://upload.imagekit.io/api/v1/files/upload"
IMAGEKIT_PRIVATE_KEY = os.getenv("IMAGEKIT_PRIVATE_KEY")
IMAGEKIT_URL_ENDPOINT = os.getenv("IMAGEKIT_URL_ENDPOINT")


def _upload_pdf_to_imagekit(pdf_bytes: bytes, filename: str) -> tuple[str, str]:
    """
    Upload PDF to ImageKit and return URL and file ID.
    
    Args:
        pdf_bytes: PDF file content as bytes
        filename: Original filename
        
    Returns:
        Tuple of (URL, file_id)
        
    Raises:
        RuntimeError: If upload fails
    """
    if not IMAGEKIT_PRIVATE_KEY:
        raise RuntimeError("IMAGEKIT_PRIVATE_KEY not configured")
    
    log_handler.info(f"Uploading PDF to ImageKit: {filename}")
    
    auth = base64.b64encode(f"{IMAGEKIT_PRIVATE_KEY}:".encode()).decode()
    
    import requests
    response = requests.post(
        IMAGEKIT_UPLOAD_URL,
        headers={"Authorization": f"Basic {auth}"},
        files={"file": (filename, pdf_bytes, "application/pdf")},
        data={
            "fileName": filename,
            "useUniqueFileName": "true"
        }
    )
    
    if response.status_code != 200:
        error_msg = f"ImageKit upload failed: {response.text}"
        log_handler.error(error_msg)
        raise RuntimeError(error_msg)
    
    data = response.json()
    log_handler.info(f"Successfully uploaded PDF to ImageKit: {data['url']}")
    return data["url"], data["fileId"]


def _delete_from_imagekit(file_id: str) -> None:
    """Delete file from ImageKit."""
    if not IMAGEKIT_PRIVATE_KEY:
        return
    
    log_handler.info(f"Deleting file from ImageKit: {file_id}")
    
    auth = base64.b64encode(f"{IMAGEKIT_PRIVATE_KEY}:".encode()).decode()
    
    import requests
    IMAGEKIT_DELETE_URL = "https://api.imagekit.io/v1/files"
    response = requests.delete(
        f"{IMAGEKIT_DELETE_URL}/{file_id}",
        headers={"Authorization": f"Basic {auth}"}
    )
    
    if response.status_code not in (200, 204):
        log_handler.warning(f"Failed to delete file from ImageKit: {response.text}")
    else:
        log_handler.info(f"Successfully deleted file from ImageKit: {file_id}")


@router.post("/documents", response_model=DocumentUploadResponse)
async def upload_document(
    company_id: str = Form(..., description="Company identifier"),
    pdf_file: Optional[UploadFile] = File(None, description="PDF file to upload"),
    pdf_url: Optional[str] = Form(None, description="URL to PDF file"),
    version: Optional[str] = Form("v1", description="Document version"),
) -> DocumentUploadResponse:
    """
    Upload a document to Tower.
    
    This endpoint accepts either:
    - A PDF file upload (multipart/form-data)
    - A PDF URL (form data)
    
    The document is processed through the document-ingestion Tower app.
    
    Args:
        company_id: Company identifier (required)
        pdf_file: PDF file to upload (optional if pdf_url provided)
        pdf_url: URL to PDF file (optional if pdf_file provided)
        version: Document version label (default: "v1")
        
    Returns:
        DocumentUploadResponse with document_id and status
        
    Raises:
        HTTPException: If validation fails or processing errors occur
    """
    log_handler.info(f"Received document upload request for company: {company_id}")
    
    # Validate company_id
    if not company_id or not company_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="company_id is required"
        )
    
    # Validate that either file or URL is provided
    if not pdf_file and not pdf_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either pdf_file or pdf_url must be provided"
        )
    
    # If both provided, prefer file upload
    if pdf_file and pdf_url:
        log_handler.warning("Both pdf_file and pdf_url provided, using pdf_file")
        pdf_url = None
    
    imagekit_file_id: Optional[str] = None
    final_pdf_url: Optional[str] = None
    
    try:
        # Handle file upload
        if pdf_file:
            # Validate file type
            if not pdf_file.filename:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="PDF file must have a filename"
                )
            
            if not pdf_file.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File must be a PDF (.pdf extension required)"
                )
            
            # Validate file size (max 50MB)
            MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
            pdf_bytes = await pdf_file.read()
            
            if len(pdf_bytes) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024):.0f}MB"
                )
            
            if len(pdf_bytes) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="PDF file is empty"
                )
            
            log_handler.info(f"Processing uploaded PDF file: {pdf_file.filename} ({len(pdf_bytes)} bytes)")
            
            # Process PDF to get metadata and verify it's valid
            try:
                pdf_result = pdf_service.process_pdf_from_bytes(
                    pdf_bytes,
                    filename=pdf_file.filename,
                    generate_chunks=False  # Don't generate chunks here, Tower will handle it
                )
                log_handler.info(f"PDF processed successfully: {pdf_result['metadata']['page_count']} pages")
            except Exception as e:
                error_msg = f"Invalid or corrupted PDF file: {str(e)}"
                log_handler.error(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
            
            # Upload to ImageKit to get a URL for Tower
            try:
                final_pdf_url, imagekit_file_id = _upload_pdf_to_imagekit(pdf_bytes, pdf_file.filename)
                log_handler.info(f"PDF uploaded to ImageKit: {final_pdf_url}")
            except Exception as e:
                error_msg = f"Failed to upload PDF to temporary storage: {str(e)}"
                log_handler.error(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_msg
                )
        
        # Handle URL
        elif pdf_url:
            # Validate URL format
            if not pdf_url.startswith(("http://", "https://")):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="pdf_url must be a valid HTTP/HTTPS URL"
                )
            
            final_pdf_url = pdf_url
            log_handler.info(f"Using provided PDF URL: {pdf_url}")
        
        # Call document-ingestion Tower app
        try:
            tower_service = get_tower_service()
            result = tower_service.call_document_ingestion(
                pdf_url=final_pdf_url,
                company_id=company_id,
                version=version or "v1",
                source_url=final_pdf_url
            )
            
            document = result.get("document", {})
            document_id = document.get("document_id", "unknown")
            
            log_handler.info(f"Document uploaded successfully: {document_id}")
            
            return DocumentUploadResponse(
                document_id=document_id,
                status="completed"
            )
            
        except Exception as e:
            error_msg = f"Error processing document with Tower: {str(e)}"
            log_handler.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        error_msg = f"Error uploading document: {str(e)}"
        log_handler.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
    
    finally:
        # Clean up ImageKit file if we uploaded one
        if imagekit_file_id:
            try:
                _delete_from_imagekit(imagekit_file_id)
            except Exception as e:
                log_handler.warning(f"Failed to cleanup ImageKit file: {e}")


# Keep backward compatibility endpoint for JSON body
@router.post("/documents/json", response_model=DocumentUploadResponse)
async def upload_document_json(payload: DocumentUploadRequest) -> DocumentUploadResponse:
    """
    Upload a document to Tower (JSON body format, backward compatibility).
    
    This endpoint accepts a PDF URL in JSON format.
    For file uploads, use the main /documents endpoint with multipart/form-data.
    
    Args:
        payload: Document upload request with company_id and optional pdf_url
        
    Returns:
        DocumentUploadResponse with document_id and status
    """
    log_handler.info(f"Received document upload request (JSON) for company: {payload.company_id}")
    
    if not payload.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="company_id is required"
        )
    
    if not payload.pdf_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="pdf_url is required. For file uploads, use /documents endpoint with multipart/form-data"
        )
    
    try:
        # Call document-ingestion Tower app
        tower_service = get_tower_service()
        result = tower_service.call_document_ingestion(
            pdf_url=payload.pdf_url,
            company_id=payload.company_id,
            version="v1",  # Default version
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
