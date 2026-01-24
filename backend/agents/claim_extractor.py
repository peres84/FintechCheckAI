from backend.services.ai_agent_service import extract_claims_from_transcript


async def extract_claims(transcript: str) -> list[dict]:
    """
    Extract claims from transcript using AI agent service.
    
    Args:
        transcript: The transcript text to analyze
        
    Returns:
        List of extracted claims
    """
    return await extract_claims_from_transcript(transcript)
