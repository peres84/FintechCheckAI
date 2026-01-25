/**
 * FinTech Check AI - API Service Layer
 * 
 * This file contains placeholder functions for all external API integrations.
 * Replace the mock implementations with actual API calls to your backend services.
 * 
 * Each function includes:
 * - TypeScript interfaces for request/response
 * - Expected API endpoint documentation
 * - Mock implementation for development/testing
 */

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

// =============================================================================
// API FUNCTIONS
// =============================================================================

/**
 * Extract transcript from a YouTube video
 * 
 * Your API should:
 * 1. First attempt to get transcript via YouTube Transcript API
 * 2. If unavailable, fall back to:
 *    - Download audio
 *    - Convert to .wav
 *    - Upload to ImageKit
 *    - Send to RunPod Whisper for transcription
 *    - Delete uploaded audio after processing
 * 
 * @param youtubeUrl - Full YouTube video URL
 * @returns TranscriptResult with transcript text and metadata
 * 
 * Expected endpoint: POST /api/extract-transcript
 * Request body: { url: string }
 * Response: TranscriptResult
 */
export async function extractTranscript(youtubeUrl: string): Promise<TranscriptResult> {
  // TODO: Replace with actual API call
  // Example:
  // const response = await fetch('YOUR_API_ENDPOINT/api/extract-transcript', {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body: JSON.stringify({ url: youtubeUrl }),
  // });
  // return response.json();

  console.log('[API] extractTranscript called with:', youtubeUrl);
  
  // Mock implementation for development
  await simulateDelay(2000);
  
  return {
    success: true,
    transcript: `This is a mock transcript for the video. In a real implementation, 
    this would contain the actual spoken content from the YouTube video. 
    The company reported record earnings this quarter with revenue up 25% year over year.
    They claim to have zero debt and strong cash reserves of over $10 billion.
    The CEO mentioned plans to expand into three new markets by next year.
    Additionally, they stated that their user base has grown to 50 million active users.`,
    segments: [
      { text: "This is a mock transcript", start: 0, duration: 3 },
      { text: "for the video.", start: 3, duration: 2 },
    ],
    source: 'youtube-api',
    videoTitle: 'Mock Video Title',
    channelName: 'Mock Channel',
  };
}

/**
 * Extract text content from a PDF document
 * 
 * @param file - PDF file to extract content from
 * @returns PDFExtractionResult with extracted text
 * 
 * Expected endpoint: POST /api/extract-pdf
 * Request body: FormData with 'file' field
 * Response: PDFExtractionResult
 */
export async function extractPdfContent(file: File): Promise<PDFExtractionResult> {
  // TODO: Replace with actual API call
  // Example:
  // const formData = new FormData();
  // formData.append('file', file);
  // const response = await fetch('YOUR_API_ENDPOINT/api/extract-pdf', {
  //   method: 'POST',
  //   body: formData,
  // });
  // return response.json();

  console.log('[API] extractPdfContent called with:', file.name);
  
  // Mock implementation for development
  await simulateDelay(1500);
  
  return {
    success: true,
    content: `Mock PDF content extracted from ${file.name}. 
    This would contain the actual text from the uploaded PDF document.
    Official financial statements, regulatory filings, or other reference documents.`,
    pageCount: 5,
    metadata: {
      title: file.name,
      author: 'Document Author',
      creationDate: new Date().toISOString(),
    },
  };
}

/**
 * Query the RAG system (Tower instance) for relevant documents
 * 
 * Your Tower instance should:
 * - Store official documents (PDFs, filings, reports)
 * - Hash documents for immutability verification
 * - Return relevant excerpts based on semantic search
 * 
 * @param query - Search query for relevant documents
 * @returns RAGQueryResult with matching documents
 * 
 * Expected endpoint: POST /api/rag/query
 * Request body: { query: string, limit?: number }
 * Response: RAGQueryResult
 */
export async function queryRAG(query: string): Promise<RAGQueryResult> {
  // TODO: Replace with actual API call
  // Example:
  // const response = await fetch('YOUR_TOWER_ENDPOINT/api/rag/query', {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body: JSON.stringify({ query, limit: 10 }),
  // });
  // return response.json();

  console.log('[API] queryRAG called with:', query);
  
  // Mock implementation for development
  await simulateDelay(1000);
  
  return {
    success: true,
    documents: [
      {
        content: 'Official SEC filing excerpt: Company reported Q3 revenue of $5.2 billion...',
        source: 'SEC 10-Q Filing 2024',
        relevanceScore: 0.95,
        hash: 'abc123def456',
      },
      {
        content: 'Annual report states: Total debt obligations reduced to $500 million...',
        source: 'Annual Report 2023',
        relevanceScore: 0.87,
        hash: 'xyz789ghi012',
      },
    ],
  };
}

/**
 * Run fact-checking analysis using AI agent
 * 
 * Your agent should:
 * - Analyze the transcript for factual claims
 * - Cross-reference claims against RAG documents
 * - Provide verdicts with evidence and confidence scores
 * 
 * @param transcript - Video transcript text
 * @param ragData - Retrieved documents from RAG system
 * @param pdfContent - Optional additional PDF content
 * @returns FactCheckResult with analyzed claims
 * 
 * Expected endpoint: POST /api/fact-check
 * Request body: { transcript: string, documents: RAGDocument[], pdfContent?: string }
 * Response: FactCheckResult
 */
export async function factCheck(
  transcript: string,
  ragData: RAGQueryResult,
  pdfContent?: string
): Promise<FactCheckResult> {
  // TODO: Replace with actual API call
  // Example:
  // const response = await fetch('YOUR_API_ENDPOINT/api/fact-check', {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body: JSON.stringify({ 
  //     transcript, 
  //     documents: ragData.documents,
  //     pdfContent 
  //   }),
  // });
  // return response.json();

  console.log('[API] factCheck called');
  
  // Mock implementation for development
  await simulateDelay(3000);
  
  return {
    success: true,
    overallScore: 72,
    summary: 'The analyzed content contains a mix of verified and unverifiable claims. Key financial figures appear accurate based on official filings, but some forward-looking statements cannot be confirmed.',
    analyzedAt: new Date().toISOString(),
    claims: [
      {
        id: '1',
        text: 'Revenue up 25% year over year',
        verdict: 'true',
        confidence: 95,
        evidence: [
          {
            source: 'SEC 10-Q Filing 2024',
            excerpt: 'Quarterly revenue increased 24.8% compared to the same period last year.',
            supportLevel: 'supports',
          },
        ],
        explanation: 'This claim is verified by official SEC filings which show 24.8% YoY growth, closely matching the stated 25%.',
        timestamp: '0:45',
      },
      {
        id: '2',
        text: 'Zero debt',
        verdict: 'false',
        confidence: 88,
        evidence: [
          {
            source: 'Annual Report 2023',
            excerpt: 'Total debt obligations reduced to $500 million.',
            supportLevel: 'contradicts',
          },
        ],
        explanation: 'Official filings indicate the company has $500 million in debt, contradicting the claim of zero debt.',
        timestamp: '1:23',
      },
      {
        id: '3',
        text: 'Cash reserves of over $10 billion',
        verdict: 'partial',
        confidence: 75,
        evidence: [
          {
            source: 'SEC 10-Q Filing 2024',
            excerpt: 'Cash and cash equivalents totaled $8.7 billion.',
            supportLevel: 'neutral',
          },
        ],
        explanation: 'The actual cash reserves are $8.7 billion, slightly below the claimed $10 billion. While substantial, the specific figure is overstated.',
        timestamp: '1:45',
      },
      {
        id: '4',
        text: 'Plans to expand into three new markets by next year',
        verdict: 'unverifiable',
        confidence: 40,
        evidence: [],
        explanation: 'No official documentation found to verify or deny expansion plans. This appears to be a forward-looking statement.',
        timestamp: '2:30',
      },
      {
        id: '5',
        text: '50 million active users',
        verdict: 'true',
        confidence: 92,
        evidence: [
          {
            source: 'Quarterly Earnings Call Transcript',
            excerpt: 'We are pleased to report that our monthly active user count has reached 51.2 million.',
            supportLevel: 'supports',
          },
        ],
        explanation: 'Official earnings call confirms 51.2 million MAUs, supporting the claimed 50 million figure.',
        timestamp: '3:15',
      },
    ],
  };
}

/**
 * Send a follow-up message to the AI agent for deeper analysis
 * 
 * This endpoint allows users to ask questions about the fact-check results
 * and get more detailed explanations or explore specific claims.
 * 
 * @param message - User's question
 * @param context - Previous analysis context (results, chat history)
 * @returns ChatResponse with agent's reply
 * 
 * Expected endpoint: POST /api/chat
 * Request body: { 
 *   message: string, 
 *   context: { 
 *     analysisId: string,
 *     chatHistory: ChatMessage[] 
 *   } 
 * }
 * Response: ChatResponse
 */
export async function chatWithAgent(
  message: string,
  context: {
    analysisId?: string;
    factCheckResult?: FactCheckResult;
    chatHistory: ChatMessage[];
  }
): Promise<ChatResponse> {
  // TODO: Replace with actual API call
  // Example:
  // const response = await fetch('YOUR_API_ENDPOINT/api/chat', {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body: JSON.stringify({ message, context }),
  // });
  // return response.json();

  console.log('[API] chatWithAgent called with:', message);
  
  // Mock implementation for development
  await simulateDelay(1500);
  
  // Simple mock responses based on keywords
  let response = "I can help you understand the fact-check results better. Could you be more specific about which claim you'd like to explore?";
  
  if (message.toLowerCase().includes('debt')) {
    response = "Regarding the debt claim: The official filings clearly show the company has $500 million in outstanding debt obligations. The claim of 'zero debt' appears to be misleading. This debt primarily consists of long-term bonds issued in 2022.";
  } else if (message.toLowerCase().includes('revenue') || message.toLowerCase().includes('earnings')) {
    response = "The revenue growth claim of 25% is well-supported. The SEC 10-Q filing shows 24.8% year-over-year growth, which rounds to the stated figure. This growth was driven primarily by their cloud services division.";
  } else if (message.toLowerCase().includes('reliable') || message.toLowerCase().includes('trust')) {
    response = "Based on my analysis, the speaker presents mostly accurate information but with some notable exaggerations. The financial figures are generally close to official records, but the 'zero debt' claim is a significant misrepresentation.";
  }
  
  return {
    success: true,
    message: response,
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
 * Simulate network delay for mock implementations
 */
function simulateDelay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
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
