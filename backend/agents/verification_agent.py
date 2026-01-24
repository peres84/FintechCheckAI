from typing import Dict, Any, List
from backend.services.ai_agent_service import compare_with_shareholder_letter


async def verify_claim(claims: List[Dict[str, Any]], shareholder_letter: str) -> Dict[str, Any]:
    """
    Verify claims against shareholder letter using AI agent service.
    
    Args:
        claims: List of claims to verify
        shareholder_letter: Official shareholder letter content
        
    Returns:
        Verification results with verdicts and citations
    """
    if not claims or not shareholder_letter:
        return {"verdict": "NOT_FOUND", "citations": []}
    
    try:
        comparison_result = await compare_with_shareholder_letter(claims, shareholder_letter)
        return comparison_result
    except Exception:
        return {"verdict": "ERROR", "citations": []}
