import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Import logging first (before using it)
from backend.core.logging import log_handler
from backend.core.config import config

# Load environment variables - try project root first, then backend directory
# Get the project root directory (parent of backend/)
project_root = Path(__file__).parent.parent.parent
backend_dir = Path(__file__).parent.parent

# Try loading from project root first, then backend directory
env_paths = [project_root / '.env', backend_dir / '.env']
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        log_handler.debug(f"Loaded .env from: {env_path}")
        break
else:
    # If no .env file found, still call load_dotenv() to load from environment
    load_dotenv()
    log_handler.debug("No .env file found, loading from environment variables only")

class AIAgentService:
    """
    AI Agent service for analyzing and comparing financial documents.
    
    This service provides methods for:
    - Extracting claims from YouTube transcripts
    - Comparing transcripts with shareholder letters
    - Generating verification reports
    """
    
    def __init__(self):
        # Get model from config, default to gpt-4o-mini if not found
        self.model = config.get("openai", {}).get("default_model", "gpt-4o-mini")
        self.max_tokens = 4000
        self._client = None
        log_handler.debug(f"AI Agent Service initialized with model: {self.model}")
    
    def _get_client(self) -> AsyncOpenAI:
        """
        Get or create OpenAI client lazily.
        
        Returns:
            AsyncOpenAI: The OpenAI client instance
            
        Raises:
            RuntimeError: If OPENAI_API_KEY is not set
        """
        if self._client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                error_msg = (
                    "OPENAI_API_KEY environment variable is not set. "
                    "Please set it in your .env file or environment variables."
                )
                log_handler.error(error_msg)
                raise RuntimeError(error_msg)
            self._client = AsyncOpenAI(api_key=api_key)
            log_handler.debug("OpenAI client initialized")
        return self._client
        
    async def extract_claims_from_transcript(self, transcript: str) -> List[Dict[str, Any]]:
        """
        Extract financial claims from a YouTube transcript.
        
        Args:
            transcript: The YouTube transcript text
            
        Returns:
            List of extracted claims with metadata
        """
        log_handler.info("Starting claim extraction from transcript")
        
        if not transcript or not transcript.strip():
            log_handler.warning("Empty transcript provided for claim extraction")
            return []
        
        try:
            prompt = f"""
            You are a financial analyst AI. Analyze the following YouTube transcript and extract specific financial claims, statements, and assertions.
            
            Focus on:
            1. Revenue figures and growth rates
            2. Profit margins and financial performance metrics
            3. User growth, engagement, or customer metrics
            4. Market share or competitive positioning claims
            5. Future projections or guidance
            6. Strategic initiatives or business changes
            7. Cost reduction or efficiency improvements
            
            For each claim, provide:
            - The exact claim/statement
            - The category (revenue, growth, users, etc.)
            - The confidence level (high/medium/low) based on how specific the claim is
            - Any numerical values mentioned
            
            Transcript:
            {transcript}
            
            Return the response as a JSON array of objects with the following structure:
            [
                {{
                    "claim": "exact statement from transcript",
                    "category": "revenue|growth|users|market|projection|strategy|costs|other",
                    "confidence": "high|medium|low",
                    "numerical_values": ["list of numbers mentioned"],
                    "context": "surrounding context for the claim"
                }}
            ]
            
            Only extract claims that are factual statements, not opinions or general commentary.
            """
            
            client = self._get_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise financial analyst AI that extracts factual claims from transcripts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.1  # Low temperature for consistency
            )
            
            content = response.choices[0].message.content
            log_handler.debug(f"OpenAI response for claim extraction: {content}")
            
            # Try to parse JSON response
            import json
            try:
                claims = json.loads(content)
                log_handler.info(f"Successfully extracted {len(claims)} claims from transcript")
                return claims
            except json.JSONDecodeError:
                log_handler.warning("Failed to parse JSON response, returning raw content")
                return [{"claim": content, "category": "other", "confidence": "low", "numerical_values": [], "context": ""}]
                
        except Exception as e:
            error_msg = f"Error extracting claims from transcript: {e}"
            log_handler.error(error_msg)
            raise RuntimeError(error_msg)
    
    async def compare_with_shareholder_letter(
        self, 
        transcript_claims: List[Dict[str, Any]], 
        shareholder_letter: str
    ) -> Dict[str, Any]:
        """
        Compare extracted claims with official shareholder letter content.
        
        Args:
            transcript_claims: List of claims extracted from transcript
            shareholder_letter: Content of the official shareholder letter
            
        Returns:
            Comparison analysis with verification results
        """
        log_handler.info("Starting comparison with shareholder letter")
        
        if not transcript_claims:
            log_handler.warning("No claims provided for comparison")
            return {"verified_claims": [], "discrepancies": [], "summary": "No claims to verify"}
        
        if not shareholder_letter or not shareholder_letter.strip():
            log_handler.warning("Empty shareholder letter provided for comparison")
            return {"verified_claims": [], "discrepancies": [], "summary": "No shareholder letter content to compare against"}
        
        try:
            # Format claims for the prompt
            claims_text = "\n".join([
                f"- {claim['claim']} (Category: {claim['category']}, Confidence: {claim['confidence']})"
                for claim in transcript_claims
            ])
            
            prompt = f"""
            You are a financial verification AI. Compare the following claims extracted from a YouTube transcript with the official shareholder letter content.
            
            CLAIMS FROM TRANSCRIPT:
            {claims_text}
            
            OFFICIAL SHAREHOLDER LETTER:
            {shareholder_letter}
            
            For each claim, determine:
            1. VERIFIED: The claim is supported by the shareholder letter
            2. CONTRADICTED: The claim contradicts information in the shareholder letter
            3. NOT_FOUND: The claim is not addressed in the shareholder letter
            4. PARTIALLY_VERIFIED: Some aspects are supported, others are not
            
            Provide specific evidence from the shareholder letter for your assessment.
            
            Return the response as JSON with this structure:
            {{
                "verified_claims": [
                    {{
                        "claim": "original claim text",
                        "status": "VERIFIED|CONTRADICTED|NOT_FOUND|PARTIALLY_VERIFIED",
                        "evidence": "specific text from shareholder letter that supports/contradicts",
                        "confidence": "high|medium|low",
                        "notes": "additional analysis or context"
                    }}
                ],
                "summary": {{
                    "total_claims": number,
                    "verified": number,
                    "contradicted": number,
                    "not_found": number,
                    "partially_verified": number,
                    "overall_accuracy": "percentage or assessment"
                }},
                "key_discrepancies": [
                    {{
                        "claim": "contradicted claim",
                        "transcript_version": "what was said in transcript",
                        "official_version": "what the shareholder letter says",
                        "severity": "high|medium|low"
                    }}
                ]
            }}
            """
            
            client = self._get_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise financial verification AI that compares claims against official documents."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            log_handler.debug(f"OpenAI response for comparison: {content}")
            
            # Try to parse JSON response
            import json
            try:
                comparison_result = json.loads(content)
                log_handler.info("Successfully completed comparison with shareholder letter")
                return comparison_result
            except json.JSONDecodeError:
                log_handler.warning("Failed to parse JSON response, returning raw content")
                return {
                    "verified_claims": [],
                    "summary": {"total_claims": len(transcript_claims), "overall_accuracy": "Unable to parse"},
                    "key_discrepancies": [],
                    "raw_response": content
                }
                
        except Exception as e:
            error_msg = f"Error comparing with shareholder letter: {e}"
            log_handler.error(error_msg)
            raise RuntimeError(error_msg)
    
    async def generate_verification_report(
        self, 
        video_url: str,
        transcript: str,
        claims: List[Dict[str, Any]],
        comparison_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive verification report.
        
        Args:
            video_url: Original YouTube video URL
            transcript: Full transcript text
            claims: Extracted claims
            comparison_result: Results from shareholder letter comparison
            
        Returns:
            Comprehensive verification report
        """
        log_handler.info("Generating comprehensive verification report")
        
        try:
            report = {
                "metadata": {
                    "video_url": video_url,
                    "analysis_timestamp": str(datetime.now()),
                    "transcript_length": len(transcript.split()) if transcript else 0,
                    "total_claims_extracted": len(claims)
                },
                "claims_analysis": {
                    "extracted_claims": claims,
                    "categories": self._categorize_claims(claims)
                },
                "verification_results": comparison_result,
                "executive_summary": self._generate_executive_summary(comparison_result),
                "recommendations": self._generate_recommendations(comparison_result)
            }
            
            log_handler.info("Successfully generated verification report")
            return report
            
        except Exception as e:
            error_msg = f"Error generating verification report: {e}"
            log_handler.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _categorize_claims(self, claims: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize claims by type."""
        categories = {}
        for claim in claims:
            category = claim.get("category", "other")
            categories[category] = categories.get(category, 0) + 1
        return categories
    
    def _generate_executive_summary(self, comparison_result: Dict[str, Any]) -> str:
        """Generate an executive summary of the verification results."""
        summary = comparison_result.get("summary", {})
        total = summary.get("total_claims", 0)
        verified = summary.get("verified", 0)
        contradicted = summary.get("contradicted", 0)
        
        if total == 0:
            return "No claims were extracted for verification."
        
        accuracy_rate = (verified / total) * 100 if total > 0 else 0
        
        summary_text = f"""
        Verification Summary:
        - Total claims analyzed: {total}
        - Verified claims: {verified} ({accuracy_rate:.1f}%)
        - Contradicted claims: {contradicted}
        - Overall assessment: {'High accuracy' if accuracy_rate >= 80 else 'Medium accuracy' if accuracy_rate >= 60 else 'Low accuracy'}
        """
        
        if contradicted > 0:
            summary_text += f"\n- Warning: {contradicted} claims were contradicted by official documents"
        
        return summary_text.strip()
    
    def _generate_recommendations(self, comparison_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on verification results."""
        recommendations = []
        
        discrepancies = comparison_result.get("key_discrepancies", [])
        summary = comparison_result.get("summary", {})
        
        if discrepancies:
            recommendations.append("Review contradicted claims for potential misinformation")
            
        if summary.get("not_found", 0) > 0:
            recommendations.append("Consider requesting clarification on unverified claims")
            
        if summary.get("verified", 0) / summary.get("total_claims", 1) < 0.5:
            recommendations.append("High number of unverified claims - exercise caution")
        
        if not recommendations:
            recommendations.append("Claims appear to be well-supported by official documents")
            
        return recommendations


# Global service instance
ai_agent_service = AIAgentService()


# Convenience functions for backward compatibility
async def extract_claims_from_transcript(transcript: str) -> List[Dict[str, Any]]:
    """Extract claims from transcript using the AI agent service."""
    return await ai_agent_service.extract_claims_from_transcript(transcript)


async def compare_with_shareholder_letter(
    transcript_claims: List[Dict[str, Any]], 
    shareholder_letter: str
) -> Dict[str, Any]:
    """Compare claims with shareholder letter using the AI agent service."""
    return await ai_agent_service.compare_with_shareholder_letter(transcript_claims, shareholder_letter)


async def generate_verification_report(
    video_url: str,
    transcript: str,
    claims: List[Dict[str, Any]],
    comparison_result: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate verification report using the AI agent service."""
    return await ai_agent_service.generate_verification_report(
        video_url, transcript, claims, comparison_result
    )