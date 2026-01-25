/**
 * FinTech Check AI - API Service Layer
 * 
 * Integrated with backend FastAPI endpoints.
 */

// =============================================================================
// CONFIGURATION
// =============================================================================

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

export interface TranscriptSegment {
  text: string;
  start: number;
  duration: number;
}

export interface TranscriptResult {
  success: boolean;
  transcript: string;
  segments: TranscriptSegment[];
  source: 'youtube-api' | 'whisper-fallback';
  videoTitle?: string;
  channelName?: string;
  error?: string;
}

export interface PDFExtractionResult {
  success: boolean;
  content: string;
  pageCount: number;
  metadata?: {
    title?: string;
    author?: string;
    creationDate?: string;
  };
  error?: string;
}

export interface RAGQueryResult {
  success: boolean;
  documents: Array<{
    content: string;
    source: string;
    relevanceScore: number;
    hash: string; // Immutable document hash from Tower
  }>;
  error?: string;
}

export type VerdictType = 'true' | 'false' | 'partial' | 'unverifiable';

export interface Claim {
  id: string;
  text: string;
  verdict: VerdictType;
  confidence: number; // 0-100
  evidence: Array<{
    source: string;
    excerpt: string;
    supportLevel: 'supports' | 'contradicts' | 'neutral';
  }>;
  explanation: string;
  timestamp?: string; // Video timestamp if available
}

export interface FactCheckResult {
  success: boolean;
  overallScore: number; // 0-100 credibility score
  claims: Claim[];
  summary: string;
  analyzedAt: string;
  error?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatResponse {
  success: boolean;
  message: string;
  error?: string;
}

export interface Company {
  company_id: string;
  name: string;
  ticker?: string;
  industry?: string;
  created_at?: string;
}

// =============================================================================
// API FUNCTIONS
// =============================================================================

/**
 * Extract transcript from a YouTube video
 * 
 * @param youtubeUrl - Full YouTube video URL
 * @returns TranscriptResult with transcript text and metadata
 */
export async function extractTranscript(youtubeUrl: string): Promise<TranscriptResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/youtube/transcript`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: youtubeUrl }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to extract transcript' }));
      return {
        success: false,
        transcript: '',
        segments: [],
        source: 'youtube-api',
        error: errorData.detail || `HTTP ${response.status}`,
      };
    }

    const data = await response.json();
    
    // Map backend response to frontend format
    return {
      success: data.status === 'completed',
      transcript: data.transcript || '',
      segments: [], // Backend doesn't return segments yet
      source: data.source === 'youtube_captions' ? 'youtube-api' : 'whisper-fallback',
      videoTitle: data.video_id, // Backend doesn't return title yet
      channelName: undefined, // Backend doesn't return channel yet
      error: data.error || undefined,
    };
  } catch (error) {
    console.error('[API] extractTranscript error:', error);
    return {
      success: false,
      transcript: '',
      segments: [],
      source: 'youtube-api',
      error: error instanceof Error ? error.message : 'Network error',
    };
  }
}

/**
 * Extract text content from a PDF document
 * 
 * Note: The backend doesn't have a direct PDF extraction endpoint.
 * We'll use the document upload endpoint and process it.
 * 
 * @param file - PDF file to extract content from
 * @returns PDFExtractionResult with extracted text
 */
export async function extractPdfContent(file: File): Promise<PDFExtractionResult> {
  try {
    // For now, we'll upload the document and note that full extraction
    // would require processing through the PDF service
    // This is a placeholder - in production, you might want a dedicated endpoint
    
    const formData = new FormData();
    formData.append('pdf_file', file);
    formData.append('company_id', 'temp'); // Temporary company ID
    
    const response = await fetch(`${API_BASE_URL}/api/documents`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to process PDF' }));
      return {
        success: false,
        content: '',
        pageCount: 0,
        error: errorData.detail || `HTTP ${response.status}`,
      };
    }

    // Note: The backend document upload doesn't return extracted content yet
    // This would need to be implemented or we'd need a separate endpoint
    // For now, return a placeholder
    return {
      success: true,
      content: `PDF uploaded successfully: ${file.name}. Full text extraction requires backend implementation.`,
      pageCount: 0,
      metadata: {
        title: file.name,
      },
    };
  } catch (error) {
    console.error('[API] extractPdfContent error:', error);
    return {
      success: false,
      content: '',
      pageCount: 0,
      error: error instanceof Error ? error.message : 'Network error',
    };
  }
}

/**
 * Query the RAG system (Tower instance) for relevant documents
 * 
 * Note: The backend doesn't have a direct RAG query endpoint.
 * RAG queries are done internally during verification.
 * This function is kept for compatibility but returns empty results.
 * 
 * @param query - Search query for relevant documents
 * @returns RAGQueryResult with matching documents
 */
export async function queryRAG(query: string): Promise<RAGQueryResult> {
  // The backend doesn't expose a direct RAG query endpoint
  // RAG queries happen internally during verification
  // Return empty result for now
  console.log('[API] queryRAG called with:', query);
  console.warn('[API] Direct RAG queries not supported. RAG is used internally during verification.');
  
  return {
    success: true,
    documents: [],
  };
}

/**
 * Run fact-checking analysis using AI agent
 * 
 * This uses the complete verification workflow endpoint which:
 * 1. Extracts transcript from YouTube
 * 2. Extracts claims
 * 3. Retrieves relevant documents via RAG
 * 4. Verifies claims against documents
 * 
 * @param transcript - Video transcript text
 * @param ragData - Retrieved documents from RAG system (not used, RAG is internal)
 * @param pdfContent - Optional additional PDF content (not used yet)
 * @returns FactCheckResult with analyzed claims
 */
export async function factCheck(
  transcript: string,
  ragData: RAGQueryResult,
  pdfContent?: string
): Promise<FactCheckResult> {
  try {
    // Extract YouTube URL from transcript if available, or use a placeholder
    // In a real scenario, we'd need to pass the YouTube URL separately
    // For now, we'll use the verify-youtube-video endpoint which handles everything
    
    // Note: This endpoint requires youtube_url and company_id
    // We need to modify the frontend to collect company_id
    // For now, return an error if company_id is not available
    
    // This is a limitation - we need the YouTube URL and company ID
    // The Analyze page should collect company_id
    throw new Error('Company ID required. Please select a company before analyzing.');
  } catch (error) {
    console.error('[API] factCheck error:', error);
    return {
      success: false,
      overallScore: 0,
      claims: [],
      summary: '',
      analyzedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Run complete verification workflow from YouTube URL
 * 
 * This is the recommended way to do fact-checking as it handles
 * the complete workflow: transcript extraction, claim extraction,
 * RAG retrieval, and verification.
 * 
 * @param youtubeUrl - YouTube video URL
 * @param companyId - Company identifier
 * @returns FactCheckResult with analyzed claims
 */
export async function verifyYouTubeVideo(
  youtubeUrl: string,
  companyId: string
): Promise<FactCheckResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/ai-agent/verify-youtube-video`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        youtube_url: youtubeUrl,
        company_id: companyId,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Verification failed' }));
      return {
        success: false,
        overallScore: 0,
        claims: [],
        summary: '',
        analyzedAt: new Date().toISOString(),
        error: errorData.detail || `HTTP ${response.status}`,
      };
    }

    const data = await response.json();
    
    // Map backend VerificationAnalysisResponse to frontend FactCheckResult
    const claims: Claim[] = (data.extracted_claims || []).map((claim: any, index: number) => {
      // Map verification result to verdict
      const verification = data.verification_results?.verified_claims?.find(
        (v: any) => v.claim?.claim === claim.claim
      );
      
      let verdict: VerdictType = 'unverifiable';
      let confidence = 50;
      let evidence: Claim['evidence'] = [];
      let explanation = 'No verification data available.';
      
      if (verification) {
        const verdictMap: Record<string, VerdictType> = {
          'VERIFIED': 'true',
          'CONTRADICTED': 'false',
          'PARTIALLY_VERIFIED': 'partial',
          'NOT_FOUND': 'unverifiable',
        };
        verdict = verdictMap[verification.verdict] || 'unverifiable';
        confidence = verification.confidence || 50;
        
        // Map citations to evidence
        evidence = (verification.citations || []).map((citation: any) => ({
          source: citation.source || 'Unknown',
          excerpt: citation.excerpt || citation.content || '',
          supportLevel: verdict === 'true' ? 'supports' : verdict === 'false' ? 'contradicts' : 'neutral',
        }));
        
        explanation = verification.explanation || verification.reasoning || '';
      }
      
      return {
        id: `claim-${index}`,
        text: claim.claim || claim.text || '',
        verdict,
        confidence,
        evidence,
        explanation,
        timestamp: claim.timestamp,
      };
    });
    
    // Calculate overall score from claims
    const overallScore = claims.length > 0
      ? Math.round(
          claims.reduce((sum, claim) => {
            const scoreMap = { true: 100, false: 0, partial: 50, unverifiable: 50 };
            return sum + (scoreMap[claim.verdict] * claim.confidence / 100);
          }, 0) / claims.length
        )
      : 0;
    
    return {
      success: true,
      overallScore,
      claims,
      summary: data.executive_summary || data.summary || 'Analysis completed.',
      analyzedAt: data.metadata?.analysis_timestamp || new Date().toISOString(),
    };
  } catch (error) {
    console.error('[API] verifyYouTubeVideo error:', error);
    return {
      success: false,
      overallScore: 0,
      claims: [],
      summary: '',
      analyzedAt: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Network error',
    };
  }
}

/**
 * Get list of available companies
 * 
 * @returns Array of Company objects
 */
export async function getCompanies(): Promise<Company[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/companies`, {
      method: 'GET',
    });

    if (!response.ok) {
      console.error('[API] getCompanies failed:', response.status);
      return [];
    }

    const data = await response.json();
    return data.companies || [];
  } catch (error) {
    console.error('[API] getCompanies error:', error);
    return [];
  }
}

/**
 * Send a follow-up message to the AI agent for deeper analysis
 * 
 * Note: The backend doesn't have a chat endpoint yet.
 * This is a placeholder for future implementation.
 * 
 * @param message - User's question
 * @param context - Previous analysis context (results, chat history)
 * @returns ChatResponse with agent's reply
 */
export async function chatWithAgent(
  message: string,
  context: {
    analysisId?: string;
    factCheckResult?: FactCheckResult;
    chatHistory: ChatMessage[];
  }
): Promise<ChatResponse> {
  // TODO: Implement when backend chat endpoint is available
  console.log('[API] chatWithAgent called with:', message);
  console.warn('[API] Chat endpoint not yet implemented in backend');
  
  // Mock response for now
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  return {
    success: false,
    message: 'Chat functionality is not yet available. This feature will be implemented in a future update.',
    error: 'Not implemented',
  };
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Validate YouTube URL format
 */
export function isValidYouTubeUrl(url: string): boolean {
  const patterns = [
    /^https?:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+/,
    /^https?:\/\/youtu\.be\/[\w-]+/,
    /^https?:\/\/(www\.)?youtube\.com\/embed\/[\w-]+/,
  ];
  return patterns.some(pattern => pattern.test(url));
}

/**
 * Extract video ID from YouTube URL
 */
export function extractVideoId(url: string): string | null {
  const patterns = [
    /youtube\.com\/watch\?v=([\w-]+)/,
    /youtu\.be\/([\w-]+)/,
    /youtube\.com\/embed\/([\w-]+)/,
  ];
  
  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) return match[1];
  }
  return null;
}

/**
 * Get verdict color class based on verdict type
 */
export function getVerdictColor(verdict: VerdictType): string {
  const colors: Record<VerdictType, string> = {
    true: 'text-success',
    false: 'text-destructive',
    partial: 'text-warning',
    unverifiable: 'text-muted-foreground',
  };
  return colors[verdict];
}

/**
 * Get verdict background color class
 */
export function getVerdictBgColor(verdict: VerdictType): string {
  const colors: Record<VerdictType, string> = {
    true: 'bg-success/10',
    false: 'bg-destructive/10',
    partial: 'bg-warning/10',
    unverifiable: 'bg-muted',
  };
  return colors[verdict];
}

/**
 * Get verdict label text
 */
export function getVerdictLabel(verdict: VerdictType): string {
  const labels: Record<VerdictType, string> = {
    true: 'True',
    false: 'False',
    partial: 'Partially True',
    unverifiable: 'Unverifiable',
  };
  return labels[verdict];
}
