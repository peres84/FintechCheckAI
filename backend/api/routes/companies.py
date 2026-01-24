from fastapi import APIRouter, HTTPException, status
from typing import List

from backend.core.logging import log_handler
from backend.models.schemas import Company, CompanyListResponse

router = APIRouter()


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
        from backend.services.tower_service import TowerService
        tower_service = TowerService()
        
        # Query distinct companies from documents table
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
            
            # Build company list (for now, use company_id as name)
            # TODO: Query companies table when it's populated
            companies = []
            for company_id in company_ids:
                if company_id:
                    companies.append(Company(
                        company_id=company_id,
                        name=company_id.title(),  # Placeholder
                        ticker=None,
                        industry=None,
                        created_at=None
                    ))
            
            # If no companies found in documents, return placeholder
            if not companies:
                companies = [
                    Company(
                        company_id="duolingo",
                        name="Duolingo",
                        ticker="DUOL",
                        industry="Education Technology",
                        created_at="2024-01-01T00:00:00Z"
                    )
                ]
        except Exception as e:
            log_handler.warning(f"Error querying Tower for companies: {e}, using placeholder")
            # Fallback to placeholder
            companies = [
                Company(
                    company_id="duolingo",
                    name="Duolingo",
                    ticker="DUOL",
                    industry="Education Technology",
                    created_at="2024-01-01T00:00:00Z"
                )
            ]
        
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
        from backend.services.tower_service import TowerService
        tower_service = TowerService()
        
        # Check if company has documents in Tower
        documents = tower_service.get_documents_by_company(company_id)
        
        if documents or company_id == "duolingo":  # Allow duolingo as fallback
            # TODO: Query companies table when it's populated
            company = Company(
                company_id=company_id,
                name=company_id.title(),  # Placeholder
                ticker=None,
                industry=None,
                created_at=None
            )
            
            # If duolingo, use known data
            if company_id == "duolingo":
                company.name = "Duolingo"
                company.ticker = "DUOL"
                company.industry = "Education Technology"
                company.created_at = "2024-01-01T00:00:00Z"
            
            return company
        else:
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
