from fastapi import APIRouter, HTTPException, status

from backend.core.logging import log_handler
from backend.models.schemas import VerificationRequest, VerificationResponse
from backend.services.ai_agent_service import ai_agent_service
from backend.services.youtube_service import fetch_transcript
from backend.services.tower_service import TowerService
from backend.services.rag_service import retrieve_chunks_from_tower
from backend.agents.verification_agent import verify_claim

router = APIRouter()
tower_service = TowerService()


@router.post("/verify", response_model=VerificationResponse)
async def verify_claims(payload: VerificationRequest) -> VerificationResponse:
    """
    Verify claims from YouTube video against company documents.
    
    This endpoint:
    1. Extracts transcript from YouTube video
    2. Extracts claims from transcript
    3. Retrieves relevant chunks from Tower for the company
    4. Verifies claims against retrieved chunks
    
    Args:
        payload: Verification request with youtube_url and company_id
        
    Returns:
        VerificationResponse with verification results
    """
    log_handler.info(f"Received verification request for company: {payload.company_id}")
    
    try:
        # Step 1: Extract transcript from YouTube
        log_handler.info("Step 1: Extracting transcript from YouTube")
        transcript_result = await fetch_transcript(payload.youtube_url)
        transcript = transcript_result.get("transcript", "")
        
        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to extract transcript from video"
            )
        
        # Step 2: Extract claims from transcript
        log_handler.info("Step 2: Extracting claims from transcript")
        claims = await ai_agent_service.extract_claims_from_transcript(transcript)
        
        if not claims:
            return VerificationResponse(results=[])
        
        # Step 3: Get documents for company from Tower
        log_handler.info(f"Step 3: Retrieving documents for company: {payload.company_id}")
        documents = tower_service.get_documents_by_company(payload.company_id)
        
        if not documents:
            log_handler.warning(f"No documents found for company: {payload.company_id}")
            return VerificationResponse(results=[])
        
        # Step 4: For each claim, retrieve relevant chunks and verify
        results = []
        for claim in claims:
            claim_text = claim.get("claim", "")
            if not claim_text:
                continue
            
            # Get the most recent document (or could iterate through all)
            latest_doc = documents[0] if documents else None
            if not latest_doc:
                continue
            
            document_id = latest_doc.get("document_id")
            
            # Retrieve relevant chunks using RAG
            log_handler.info(f"Step 4: Retrieving chunks for claim: {claim_text[:50]}...")
            chunks = retrieve_chunks_from_tower(
                document_id=document_id,
                query=claim_text,
                top_k=3
            )
            
            # Verify claim against chunks
            if chunks:
                # Use chunks as "shareholder letter" content
                chunk_content = "\n\n".join([
                    chunk.get("content", "") for chunk in chunks
                ])
                
                verification_result = await verify_claim([claim], chunk_content)
                results.append({
                    "claim": claim,
                    "verification": verification_result,
                    "chunks": chunks,
                    "document_id": document_id
                })
            else:
                results.append({
                    "claim": claim,
                    "verification": {"verdict": "NOT_FOUND", "citations": []},
                    "chunks": [],
                    "document_id": document_id
                })
        
        log_handler.info(f"Verification completed: {len(results)} results")
        return VerificationResponse(results=results)
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error in verification: {str(e)}"
        log_handler.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
