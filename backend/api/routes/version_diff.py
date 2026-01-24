from fastapi import APIRouter, HTTPException, status

from backend.core.logging import log_handler
from backend.models.schemas import VersionDiffRequest, VersionDiffResponse, DocumentVersion, ChangedSection

router = APIRouter()


@router.post(
    "/version-diff",
    response_model=VersionDiffResponse,
    summary="Compare two document versions",
    description="Compare two versions of a company document and return changed sections"
)
async def compare_versions(request: VersionDiffRequest) -> VersionDiffResponse:
    """
    Compare two document versions.
    
    This endpoint compares two versions of a document for a company and
    returns a list of changed sections with the differences.
    
    Args:
        request: Version diff request with company_id and two document IDs
        
    Returns:
        VersionDiffResponse: Comparison results with changed sections
        
    Raises:
        HTTPException: If documents not found or comparison fails
    """
    log_handler.info(
        f"Received version diff request for company {request.company_id}: "
        f"{request.document_id_1} vs {request.document_id_2}"
    )
    
    try:
        # TODO: Replace with actual Tower queries and diff logic when Tower apps are implemented
        # For now, return placeholder data
        
        # Validate that documents exist (placeholder check)
        if not request.document_id_1 or not request.document_id_2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both document IDs are required"
            )
        
        # Placeholder document versions
        doc1 = DocumentVersion(
            document_id=request.document_id_1,
            version="Q3-2024",
            sha256="placeholder_sha256_1",
            created_at="2024-09-30T00:00:00Z",
            page_count=50
        )
        
        doc2 = DocumentVersion(
            document_id=request.document_id_2,
            version="Q2-2024",
            sha256="placeholder_sha256_2",
            created_at="2024-06-30T00:00:00Z",
            page_count=48
        )
        
        # Placeholder changed sections
        # TODO: Implement actual diff algorithm when documents are available
        changed_sections: list[ChangedSection] = []
        
        response = VersionDiffResponse(
            company_id=request.company_id,
            document_1=doc1,
            document_2=doc2,
            changed_sections=changed_sections,
            total_changes=len(changed_sections)
        )
        
        log_handler.info(f"Version diff completed: {len(changed_sections)} changes found")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error comparing document versions: {str(e)}"
        log_handler.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@router.get("/version-diff/health")
def version_diff_health() -> dict:
    """Health check endpoint for version diff service."""
    log_handler.debug("Version diff service health check accessed")
    return {
        "status": "ok",
        "service": "Version Diff Service",
        "endpoints": [
            "/version-diff"
        ]
    }
