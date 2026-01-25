from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime

from backend.core.logging import log_handler
from backend.models.schemas import Company, CompanyListResponse

router = APIRouter()


def get_tower_service():
    """Get Tower service instance (lazy initialization)."""
    try:
        from backend.services.tower_service import TowerService
        return TowerService()
    except RuntimeError as e:
        log_handler.warning(f"Tower service unavailable: {e}")
        return None


def get_default_companies() -> List[Company]:
    """
    Get default list of companies.
    
    Returns a list of predefined companies that are available in the system.
    """
    return [
        Company(
            company_id="duolingo",
            name="Duolingo",
            ticker="DUOL",
            industry="Education Technology",
            created_at="2024-01-01T00:00:00Z"
        ),
        Company(
            company_id="tesla",
            name="Tesla",
            ticker="TSLA",
            industry="Electric Vehicles & Energy",
            created_at="2024-01-01T00:00:00Z"
        ),
        Company(
            company_id="openai",
            name="OpenAI",
            ticker=None,  # OpenAI is private
            industry="Artificial Intelligence",
            created_at="2024-01-01T00:00:00Z"
        )
    ]


@router.get(
    "/companies",
    response_model=CompanyListResponse,
    summary="List all companies",
    description="Get a list of all companies in the system"
)
async def list_companies() -> CompanyListResponse:
    """
    List all companies.
    
    Returns a list of all companies that have documents in the system.
    For now, returns a placeholder list. In production, this would query
    the Tower companies table.
    
    Returns:
        CompanyListResponse: List of companies with metadata
        
    Raises:
        HTTPException: If the request fails
    """
    log_handler.info("Received request to list companies")
    
    try:
        # Try to get Tower service (may be None if unavailable)
        tower_service = get_tower_service()
        
        companies_dict = {}
        
        # Start with default companies
        for default_company in get_default_companies():
            companies_dict[default_company.company_id] = default_company
        
        # If Tower is available, try to query for additional companies
        if tower_service is not None:
            try:
                sql = "SELECT DISTINCT company_id FROM documents"
                result = tower_service._client.execute_sql(sql)
                
                # Get unique company IDs
                company_ids = set()
                if isinstance(result, list):
                    for row in result:
                        if isinstance(row, dict):
                            company_ids.add(row.get("company_id"))
                        elif isinstance(row, (list, tuple)) and len(row) > 0:
                            company_ids.add(row[0])
                
                # Add any companies found in documents (preserve defaults)
                for company_id in company_ids:
                    if company_id:
                        # Only add if not already in defaults (to preserve default company data)
                        if company_id not in companies_dict:
                            companies_dict[company_id] = Company(
                                company_id=company_id,
                                name=company_id.title(),  # Placeholder
                                ticker=None,
                                industry=None,
                                created_at=None
                            )
            except Exception as e:
                log_handler.warning(f"Error querying Tower for companies: {e}, using default companies only")
        
        companies = list(companies_dict.values())
        
        # Sort by name for consistent ordering
        companies.sort(key=lambda x: x.name)
        
        response = CompanyListResponse(
            companies=companies,
            total=len(companies)
        )
        
        log_handler.info(f"Returning {len(companies)} companies")
        return response
        
    except Exception as e:
        error_msg = f"Error listing companies: {str(e)}"
        log_handler.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@router.get(
    "/companies/{company_id}",
    response_model=Company,
    summary="Get company by ID",
    description="Get detailed information about a specific company"
)
async def get_company(company_id: str) -> Company:
    """
    Get company by ID.
    
    Args:
        company_id: Unique identifier for the company
        
    Returns:
        Company: Company information
        
    Raises:
        HTTPException: If company not found or request fails
    """
    log_handler.info(f"Received request for company: {company_id}")
    
    try:
        # Check if it's a default company first
        default_companies = {c.company_id: c for c in get_default_companies()}
        
        if company_id in default_companies:
            return default_companies[company_id]
        
        # Try to get Tower service (may be None if unavailable)
        tower_service = get_tower_service()
        
        # If Tower is available, check for documents
        if tower_service is not None:
            try:
                documents = tower_service.get_documents_by_company(company_id)
                if documents:
                    # Company has documents, return placeholder data
                    return Company(
                        company_id=company_id,
                        name=company_id.title(),  # Placeholder
                        ticker=None,
                        industry=None,
                        created_at=None
                    )
            except Exception as e:
                log_handler.warning(f"Error checking Tower for company {company_id}: {e}")
        
        # Company not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company '{company_id}' not found"
        )
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error getting company: {str(e)}"
        log_handler.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@router.get("/companies/health")
def companies_health() -> dict:
    """Health check endpoint for companies service."""
    log_handler.debug("Companies service health check accessed")
    return {
        "status": "ok",
        "service": "Companies Service",
        "endpoints": [
            "/companies",
            "/companies/{company_id}"
        ]
    }
