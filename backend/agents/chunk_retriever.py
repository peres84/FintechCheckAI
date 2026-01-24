from typing import Any, Optional
from backend.services.rag_service import retrieve_chunks_from_tower, retrieve_chunks_simple
from backend.core.logging import log_handler


async def retrieve_chunks(
    claim: str,
    document_id: Optional[str] = None,
    company_id: Optional[str] = None,
    top_k: int = 5
) -> list[dict[str, Any]]:
    """
    Retrieve relevant chunks for a claim using RAG.
    
    Args:
        claim: The claim text to find relevant chunks for
        document_id: Optional document ID to search within
        company_id: Optional company ID (not yet used, for future filtering)
        top_k: Number of top chunks to return
        
    Returns:
        List of relevant chunks with scores
    """
    log_handler.info(f"Retrieving chunks for claim: {claim[:100]}...")
    
    # If document_id provided, try Tower RAG first
    if document_id:
        try:
            chunks = retrieve_chunks_from_tower(
                document_id=document_id,
                query=claim,
                top_k=top_k
            )
            if chunks:
                log_handler.info(f"Retrieved {len(chunks)} chunks from Tower")
                return chunks
        except Exception as e:
            log_handler.warning(f"Tower RAG failed: {e}, returning empty list")
    
    # Fallback: return empty list (no chunks available without document_id)
    log_handler.warning("No document_id provided, cannot retrieve chunks")
    return []
