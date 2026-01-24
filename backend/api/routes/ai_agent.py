from fastapi import APIRouter, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse

# Import logging and config
from backend.core.logging import log_handler
from backend.core.config import config

# Import services and models
from backend.services.ai_agent_service import ai_agent_service
from backend.services.youtube_service import fetch_transcript
from backend.services.opik_service import get_opik_service
from backend.models.schemas import (
    ClaimExtractionRequest, ClaimExtractionResponse,
    VerificationAnalysisRequest, VerificationAnalysisResponse,
    ComparisonRequest, ComparisonResponse
)
from backend.api.middleware.rate_limit import rate_limit_by_tag

router = APIRouter()
opik_service = get_opik_service()


@router.post(
    "/extract-claims",
    response_model=ClaimExtractionResponse,
    summary="Extract financial claims from transcript",
    description="Extract specific financial claims and assertions from a text transcript using AI analysis"
)
@rate_limit_by_tag("ai-agent")
async def extract_claims(request: ClaimExtractionRequest) -> ClaimExtractionResponse:
    """
    Extract financial claims from a transcript.
    
    This endpoint uses AI to analyze transcript text and extract specific
    financial claims, statements, and assertions with categorization.
    
    Args:
        request: Claim extraction request containing the transcript text
        
    Returns:
        ClaimExtractionResponse: Contains extracted claims with metadata
        
    Raises:
        HTTPException: If the transcript is invalid or extraction fails
    """
    log_handler.info("Received claim extraction request")
    
    if not request.transcript or not request.transcript.strip():
        error_msg = "Empty transcript provided"
        log_handler.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    try:
        # Extract claims using AI service
        claims = await ai_agent_service.extract_claims_from_transcript(request.transcript)
        
        # Track with Opik
        opik_service.track_claim_extraction(
            transcript=request.transcript,
            claims=claims,
            metadata={"endpoint": "/extract-claims"}
        )
        
        # Categorize claims
        categories = {}
        for claim in claims:
            category = claim.get("category", "other")
            categories[category] = categories.get(category, 0) + 1
        
        response = ClaimExtractionResponse(
            claims=claims,
            total_claims=len(claims),
            categories=categories
        )
        
        log_handler.info(f"Successfully extracted {len(claims)} claims")
        return response
        
    except Exception as e:
        error_msg = f"Error extracting claims: {str(e)}"
        log_handler.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@router.post(
    "/compare-claims",
    response_model=ComparisonResponse,
    summary="Compare claims with shareholder letter",
    description="Compare extracted claims against official shareholder letter content for verification"
)
async def compare_claims(request: ComparisonRequest) -> ComparisonResponse:
    """
    Compare extracted claims with official shareholder letter.
    
    This endpoint verifies claims against official documentation to identify
    verified, contradicted, or unverified statements.
    
    Args:
        request: Comparison request containing claims and shareholder letter
        
    Returns:
        ComparisonResponse: Contains verification results and discrepancies
        
    Raises:
        HTTPException: If the request is invalid or comparison fails
    """
    log_handler.info("Received claim comparison request")
    
    if not request.claims:
        error_msg = "No claims provided for comparison"
        log_handler.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    if not request.shareholder_letter or not request.shareholder_letter.strip():
        error_msg = "Empty shareholder letter provided"
        log_handler.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    try:
        # Compare claims with shareholder letter
        comparison_result = await ai_agent_service.compare_with_shareholder_letter(
            request.claims, 
            request.shareholder_letter
        )
        
        response = ComparisonResponse(
            verified_claims=comparison_result.get("verified_claims", []),
            summary=comparison_result.get("summary", {}),
            key_discrepancies=comparison_result.get("key_discrepancies", [])
        )
        
        log_handler.info("Successfully completed claim comparison")
        return response
        
    except Exception as e:
        error_msg = f"Error comparing claims: {str(e)}"
        log_handler.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@router.post(
    "/verify-youtube-video",
    response_model=VerificationAnalysisResponse,
    summary="Complete verification analysis of YouTube video",
    description="Extract transcript, analyze claims, and optionally compare with shareholder letter in one workflow"
)
async def verify_youtube_video(request: VerificationAnalysisRequest) -> VerificationAnalysisResponse:
    """
    Complete verification analysis of a YouTube video.
    
    This endpoint performs the full workflow:
    1. Extract transcript from YouTube video
    2. Extract financial claims from transcript
    3. Compare claims with shareholder letter (if provided)
    4. Generate comprehensive verification report
    
    Args:
        request: Verification analysis request with YouTube URL and optional shareholder letter
        
    Returns:
        VerificationAnalysisResponse: Complete analysis with verification results
        
    Raises:
        HTTPException: If the video URL is invalid or analysis fails
    """
    video_url = str(request.youtube_url)
    log_handler.info(f"Received complete verification request for video: {video_url}")
    
    try:
        # Step 1: Extract transcript from YouTube video
        log_handler.info("Step 1: Extracting transcript from YouTube video")
        transcript_result = await fetch_transcript(video_url)
        
        transcript = transcript_result.get("transcript", "")
        video_id = transcript_result.get("video_id", "")
        
        if not transcript:
            error_msg = "Failed to extract transcript from video"
            log_handler.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Step 2: Extract claims from transcript
        log_handler.info("Step 2: Extracting claims from transcript")
        claims = await ai_agent_service.extract_claims_from_transcript(transcript)
        
        # Track claim extraction with Opik
        opik_service.track_claim_extraction(
            transcript=transcript,
            claims=claims,
            metadata={"video_id": video_id, "endpoint": "/verify-youtube-video"}
        )
        
        # Step 3: Compare with shareholder letter (if provided)
        verification_results = {}
        if request.shareholder_letter and request.shareholder_letter.strip():
            log_handler.info("Step 3: Comparing claims with shareholder letter")
            verification_results = await ai_agent_service.compare_with_shareholder_letter(
                claims, 
                request.shareholder_letter
            )
            
            # Track verification with Opik
            for claim in claims:
                verdict = "VERIFIED" if any(
                    vc.get("status") == "VERIFIED" 
                    for vc in verification_results.get("verified_claims", [])
                    if vc.get("claim") == claim.get("claim")
                ) else "NOT_VERIFIED"
                
                opik_service.track_verification(
                    claim=claim.get("claim", ""),
                    chunks=[],
                    verdict=verdict,
                    reasoning=f"Compared against shareholder letter",
                    metadata={"video_id": video_id}
                )
        else:
            log_handler.info("Step 3: Skipped - no shareholder letter provided")
            verification_results = {
                "verified_claims": [],
                "summary": {"total_claims": len(claims), "note": "No shareholder letter provided for comparison"},
                "key_discrepancies": []
            }
        
        # Step 4: Generate comprehensive report
        log_handler.info("Step 4: Generating verification report")
        report = await ai_agent_service.generate_verification_report(
            video_url, transcript, claims, verification_results
        )
        
        # Create response
        response = VerificationAnalysisResponse(
            video_id=video_id,
            video_url=video_url,
            transcript=transcript,
            extracted_claims=claims,
            verification_results=verification_results,
            executive_summary=report.get("executive_summary", ""),
            recommendations=report.get("recommendations", []),
            metadata=report.get("metadata", {})
        )
        
        log_handler.info(f"Successfully completed verification analysis for video {video_id}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        error_msg = f"Error in verification analysis: {str(e)}"
        log_handler.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@router.post(
    "/verify-from-files",
    response_model=VerificationAnalysisResponse,
    summary="Complete verification analysis from uploaded .txt files",
    description="Upload transcript and shareholder letter as .txt files, then perform complete verification analysis"
)
async def verify_from_files(
    transcript_file: UploadFile = File(..., description="Transcript .txt file"),
    shareholder_letter_file: UploadFile = File(None, description="Shareholder letter .txt file (optional)")
) -> VerificationAnalysisResponse:
    """
    Complete verification analysis from uploaded .txt files.
    
    This endpoint accepts two .txt file uploads:
    1. Transcript file (required) - contains the YouTube transcript or other transcript text
    2. Shareholder letter file (optional) - contains the official shareholder letter text
    
    The endpoint performs the full workflow:
    1. Read transcript from uploaded file
    2. Extract financial claims from transcript
    3. Compare claims with shareholder letter (if provided)
    4. Generate comprehensive verification report
    
    Args:
        transcript_file: Uploaded .txt file containing the transcript
        shareholder_letter_file: Optional uploaded .txt file containing the shareholder letter
        
    Returns:
        VerificationAnalysisResponse: Complete analysis with verification results
        
    Raises:
        HTTPException: If files are invalid or analysis fails
    """
    log_handler.info("Received file upload verification request")
    
    # Validate transcript file
    if not transcript_file.filename:
        error_msg = "Transcript file is required"
        log_handler.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    if not transcript_file.filename.endswith('.txt'):
        error_msg = "Transcript file must be a .txt file"
        log_handler.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Validate shareholder letter file if provided
    shareholder_letter_text = None
    if shareholder_letter_file and shareholder_letter_file.filename:
        if not shareholder_letter_file.filename.endswith('.txt'):
            error_msg = "Shareholder letter file must be a .txt file"
            log_handler.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    
    try:
        # Step 1: Read transcript file
        log_handler.info(f"Reading transcript file: {transcript_file.filename}")
        transcript_content = await transcript_file.read()
        transcript = transcript_content.decode('utf-8')
        
        if not transcript or not transcript.strip():
            error_msg = "Transcript file is empty"
            log_handler.error(error_msg)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Step 2: Read shareholder letter file if provided
        if shareholder_letter_file and shareholder_letter_file.filename:
            log_handler.info(f"Reading shareholder letter file: {shareholder_letter_file.filename}")
            shareholder_letter_content = await shareholder_letter_file.read()
            shareholder_letter_text = shareholder_letter_content.decode('utf-8')
        
        # Step 3: Extract claims from transcript
        log_handler.info("Step 1: Extracting claims from transcript")
        claims = await ai_agent_service.extract_claims_from_transcript(transcript)
        
        # Step 4: Compare with shareholder letter (if provided)
        verification_results = {}
        if shareholder_letter_text and shareholder_letter_text.strip():
            log_handler.info("Step 2: Comparing claims with shareholder letter")
            verification_results = await ai_agent_service.compare_with_shareholder_letter(
                claims, 
                shareholder_letter_text
            )
        else:
            log_handler.info("Step 2: Skipped - no shareholder letter provided")
            verification_results = {
                "verified_claims": [],
                "summary": {"total_claims": len(claims), "note": "No shareholder letter provided for comparison"},
                "key_discrepancies": []
            }
        
        # Step 5: Generate comprehensive report
        log_handler.info("Step 3: Generating verification report")
        # Use a placeholder URL since we're working with files
        video_url = f"file://{transcript_file.filename}"
        report = await ai_agent_service.generate_verification_report(
            video_url, transcript, claims, verification_results
        )
        
        # Create response
        response = VerificationAnalysisResponse(
            video_id=transcript_file.filename,
            video_url=video_url,
            transcript=transcript,
            extracted_claims=claims,
            verification_results=verification_results,
            executive_summary=report.get("executive_summary", ""),
            recommendations=report.get("recommendations", []),
            metadata=report.get("metadata", {})
        )
        
        log_handler.info(f"Successfully completed verification analysis from files")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except UnicodeDecodeError as e:
        error_msg = f"Error decoding file content (must be UTF-8): {str(e)}"
        log_handler.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        error_msg = f"Error in file-based verification analysis: {str(e)}"
        log_handler.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@router.get("/health")
def ai_agent_health() -> dict:
    """Health check endpoint for AI Agent service."""
    log_handler.debug("AI Agent service health check accessed")
    from backend.core.config import config
    model = config.get("openai", {}).get("default_model", "gpt-4o-mini")
    return {
        "status": "ok", 
        "service": "AI Agent Service",
        "endpoints": [
            "/extract-claims",
            "/compare-claims", 
            "/verify-youtube-video",
            "/verify-from-files"
        ],
        "ai_model": model
    }