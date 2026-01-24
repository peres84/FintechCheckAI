from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse

# Import logging and config
from backend.core.logging import log_handler
from backend.core.config import config

# Import service and models
from backend.services.youtube_service import fetch_transcript
from backend.models.schemas import YouTubeTranscriptRequest, YouTubeTranscriptResponse
from backend.api.middleware.rate_limit import rate_limit_by_tag

router = APIRouter()


@router.post(
    config["endpoints"]["youtube_endpoint"]["transcript_route"],
    response_model=YouTubeTranscriptResponse,
    summary="Extract transcript from YouTube video",
    description="Extract transcript from a YouTube video using either YouTube captions or audio transcription"
)
@rate_limit_by_tag("youtube")
async def get_transcript(request: YouTubeTranscriptRequest) -> YouTubeTranscriptResponse:
    """
    Extract transcript from a YouTube video.
    
    This endpoint attempts to extract transcript from YouTube captions first.
    If captions are not available, it downloads the audio and transcribes it using AI.
    
    Args:
        request: YouTube transcript request containing the video URL
        
    Returns:
        YouTubeTranscriptResponse: Contains the transcript and metadata
        
    Raises:
        HTTPException: If the video URL is invalid or transcription fails
    """
    video_url = str(request.url)
    log_handler.info(f"Received transcript request for URL: {video_url}")
    
    try:
        # Call the service function
        result = await fetch_transcript(video_url)
        
        # Create response
        response = YouTubeTranscriptResponse(
            video_id=result["video_id"],
            video_url=video_url,
            transcript=result.get("transcript", ""),
            source=result.get("source", "unknown"),
            status=result.get("status", "completed"),
            error=result.get("error")
        )
        
        log_handler.info(f"Successfully processed transcript for video {result['video_id']}")
        return response
        
    except ValueError as e:
        error_msg = f"Invalid YouTube URL: {str(e)}"
        log_handler.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
        
    except RuntimeError as e:
        error_msg = f"Transcription service error: {str(e)}"
        log_handler.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
        
    except Exception as e:
        error_msg = f"Unexpected error processing transcript: {str(e)}"
        log_handler.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while processing the request"
        )


@router.get("/health")
def youtube_health() -> dict:
    """Health check endpoint for YouTube service."""
    log_handler.debug("YouTube service health check accessed")
    return {
        "status": "ok", 
        "service": "YouTube Transcript Service",
        "endpoints": [
            config["endpoints"]["youtube_endpoint"]["transcript_route"]
        ]
    }
