"""
Rate limiting middleware for FastAPI.

Uses slowapi for rate limiting functionality.
"""
from typing import Callable
from fastapi import Request, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.core.logging import log_handler
from backend.core.config import config

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)

# Rate limit configuration from config.json
def get_rate_limit_config(endpoint_tag: str) -> tuple[int, str]:
    """
    Get rate limit configuration for an endpoint tag.
    
    Args:
        endpoint_tag: Tag from config.json (e.g., "youtube", "ai-agent")
        
    Returns:
        Tuple of (limit, time_unit) where time_unit is "minute" or "second"
    """
    endpoints_config = config.get("endpoints", {})
    
    # Find endpoint config by tag
    for endpoint_key, endpoint_config in endpoints_config.items():
        if endpoint_config.get("endpoint_tag") == endpoint_tag:
            limit = endpoint_config.get("request_limit", 10)
            time_unit = endpoint_config.get("unit_of_time_for_limit", "minute")
            return limit, time_unit
    
    # Default rate limit
    return 10, "minute"


def create_rate_limit_string(limit: int, time_unit: str) -> str:
    """
    Create rate limit string for slowapi.
    
    Args:
        limit: Number of requests
        time_unit: "minute" or "second"
        
    Returns:
        Rate limit string (e.g., "10/minute")
    """
    if time_unit == "minute":
        return f"{limit}/minute"
    elif time_unit == "second":
        return f"{limit}/second"
    else:
        # Default to minute
        return f"{limit}/minute"


def setup_rate_limiting(app):
    """
    Setup rate limiting for the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    # Add rate limit exception handler
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    log_handler.info("Rate limiting middleware configured")


def rate_limit_by_tag(endpoint_tag: str):
    """
    Decorator factory for rate limiting by endpoint tag.
    
    Args:
        endpoint_tag: Tag from config.json
        
    Returns:
        Decorator function
    """
    limit, time_unit = get_rate_limit_config(endpoint_tag)
    rate_limit_str = create_rate_limit_string(limit, time_unit)
    
    log_handler.debug(f"Rate limit for {endpoint_tag}: {rate_limit_str}")
    
    return limiter.limit(rate_limit_str)
