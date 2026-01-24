import os
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
project_root = Path(__file__).parent.parent.parent
backend_dir = Path(__file__).parent.parent
env_paths = [project_root / '.env', backend_dir / '.env']
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        break
else:
    load_dotenv()

# Import logging
from backend.core.logging import log_handler
from backend.core.config import config

logger = logging.getLogger(__name__)

# Try to import Opik, but make it optional if not installed
try:
    from opik import Opik
    from opik.decorators import track
    OPIK_AVAILABLE = True
except ImportError:
    OPIK_AVAILABLE = False
    log_handler.warning("Opik SDK not installed. Opik tracking will be disabled.")
    # Create dummy decorator
    def track(name: str):
        def decorator(func):
            return func
        return decorator


class OpikService:
    """Service for Opik telemetry and tracking."""

    def __init__(self):
        """Initialize Opik client."""
        self.client = None
        self.enabled = False
        
        if not OPIK_AVAILABLE:
            log_handler.warning("Opik SDK not available. Service will run in no-op mode.")
            return
        
        try:
            # Get Opik config from environment or config.json
            opik_workspace = os.getenv("OPIK_WORKSPACE") or config.get("opik", {}).get("workspace", "fintech-check-ai")
            opik_api_key = os.getenv("OPIK_API_KEY")
            
            if not opik_api_key:
                log_handler.warning("OPIK_API_KEY not set. Opik service will run in no-op mode.")
                return
            
            self.client = Opik(
                workspace=opik_workspace,
                api_key=opik_api_key
            )
            self.enabled = True
            log_handler.info(f"Opik initialized with workspace: {opik_workspace}")
        except Exception as e:
            log_handler.error(f"Failed to initialize Opik: {e}")
            log_handler.warning("Opik service will run in no-op mode.")
            # Don't raise - allow service to continue without Opik

    @track(name="claim_extraction")
    def track_claim_extraction(
        self,
        transcript: str,
        claims: list,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track claim extraction from transcript.

        Args:
            transcript: Input transcript text
            claims: Extracted claims
            metadata: Additional metadata

        Returns:
            Tracking data
        """
        tracking_data = {
            "input": {
                "transcript_length": len(transcript),
                "transcript_preview": transcript[:200] if transcript else ""
            },
            "output": {
                "claims_count": len(claims) if claims else 0,
                "claims": claims or []
            }
        }

        if metadata:
            tracking_data["metadata"] = metadata

        if self.enabled:
            log_handler.debug(f"Tracked claim extraction: {len(claims) if claims else 0} claims")
        else:
            log_handler.debug(f"Opik disabled - would track claim extraction: {len(claims) if claims else 0} claims")
        
        return tracking_data

    @track(name="chunk_retrieval")
    def track_chunk_retrieval(
        self,
        query: str,
        chunks: list,
        scores: list,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track chunk retrieval for RAG.

        Args:
            query: Search query
            chunks: Retrieved chunks
            scores: Relevance scores
            metadata: Additional metadata

        Returns:
            Tracking data
        """
        avg_score = sum(scores) / len(scores) if scores and len(scores) > 0 else 0.0
        
        tracking_data = {
            "input": {"query": query},
            "output": {
                "chunks_count": len(chunks) if chunks else 0,
                "avg_score": avg_score,
                "chunks": chunks or []
            }
        }

        if metadata:
            tracking_data["metadata"] = metadata

        if self.enabled:
            log_handler.debug(f"Tracked chunk retrieval: {len(chunks) if chunks else 0} chunks")
        else:
            log_handler.debug(f"Opik disabled - would track chunk retrieval: {len(chunks) if chunks else 0} chunks")
        
        return tracking_data

    @track(name="verification")
    def track_verification(
        self,
        claim: str,
        chunks: list,
        verdict: str,
        reasoning: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track claim verification.

        Args:
            claim: Claim to verify
            chunks: Retrieved context chunks
            verdict: Verification verdict
            reasoning: Verification reasoning
            metadata: Additional metadata

        Returns:
            Tracking data
        """
        tracking_data = {
            "input": {"claim": claim},
            "context": {"chunks": chunks or []},
            "output": {
                "verdict": verdict,
                "reasoning": reasoning
            }
        }

        if metadata:
            tracking_data["metadata"] = metadata

        if self.enabled:
            log_handler.debug(f"Tracked verification: {verdict}")
        else:
            log_handler.debug(f"Opik disabled - would track verification: {verdict}")
        
        return tracking_data

    def track_llm_call(
        self,
        model: str,
        prompt: str,
        response: str,
        tokens_used: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track LLM API call.

        Args:
            model: Model name used
            prompt: Input prompt
            response: LLM response
            tokens_used: Number of tokens used
            metadata: Additional metadata

        Returns:
            Tracking data
        """
        tracking_data = {
            "model": model,
            "input": {
                "prompt_length": len(prompt),
                "prompt_preview": prompt[:200] if prompt else ""
            },
            "output": {
                "response_length": len(response),
                "response_preview": response[:200] if response else ""
            }
        }

        if tokens_used:
            tracking_data["tokens_used"] = tokens_used

        if metadata:
            tracking_data["metadata"] = metadata

        if self.enabled:
            log_handler.debug(f"Tracked LLM call: {model}, tokens: {tokens_used or 'unknown'}")
        else:
            log_handler.debug(f"Opik disabled - would track LLM call: {model}")
        
        return tracking_data

    def log_error(
        self,
        operation: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log error to Opik.

        Args:
            operation: Operation that failed
            error: Exception that occurred
            context: Additional context
        """
        error_data = {
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }

        log_handler.error(f"Opik error log: {error_data}")
        # Opik will automatically capture this through decorators if enabled

    def is_enabled(self) -> bool:
        """Check if Opik is enabled and available."""
        return self.enabled and self.client is not None


# Global instance - lazy initialization
_opik_service_instance = None

def get_opik_service() -> OpikService:
    """Get or create the global Opik service instance."""
    global _opik_service_instance
    if _opik_service_instance is None:
        _opik_service_instance = OpikService()
    return _opik_service_instance

# For backward compatibility
opik_service = get_opik_service()
