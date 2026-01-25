# API Documentation

Complete API reference for FinTech Check AI backend service.

## Base URL

- **Development**: `http://127.0.0.1:8000`
- **Production**: TBD

## Authentication

Currently, the API does not require authentication. Future versions may implement API key authentication.

## Rate Limiting

Rate limiting is configured per endpoint group:

- **YouTube endpoints**: 10 requests per minute
- **AI Agent endpoints**: 5 requests per minute
- **Root endpoints**: 25 requests per minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when rate limit resets

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

---

## Endpoints

### Health Check

#### `GET /health`

Check if the API is operational.

**Response:**
```json
{
  "status": "ok",
  "service": "FinTech Check AI"
}
```

---

### YouTube Transcript Extraction

#### `POST /api/youtube/transcript`

Extract transcript from a YouTube video.

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

**Response:**
```json
{
  "video_id": "VIDEO_ID",
  "video_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "transcript": "Full transcript text...",
  "source": "youtube_captions",
  "status": "completed",
  "error": null
}
```

**Sources:**
- `youtube_captions`: Extracted from YouTube's built-in captions (fast)
- `audio_transcription`: Fallback using RunPod Whisper AI transcription (slower)

**Error Responses:**
- `400`: Invalid YouTube URL
- `500`: Transcription service unavailable

#### `GET /api/youtube/health`

Check YouTube service health status.

**Response:**
```json
{
  "status": "ok",
  "service": "YouTube Transcript Service",
  "endpoints": ["/transcript", "/health"]
}
```

---

### AI Agent Endpoints

#### `POST /api/ai-agent/extract-claims`

Extract financial claims from a transcript.

**Request Body:**
```json
{
  "transcript": "Our revenue grew by 25% this quarter, reaching $100 million..."
}
```

**Response:**
```json
{
  "claims": [
    {
      "claim": "Revenue grew by 25% this quarter",
      "category": "revenue",
      "confidence": "high",
      "numerical_values": ["25%"],
      "context": "quarterly financial performance"
    }
  ],
  "total_claims": 1,
  "categories": {
    "revenue": 1
  }
}
```

**Claim Categories:**
- `revenue`: Revenue figures and growth
- `profit`: Profit margins and financial metrics
- `users`: User growth and engagement
- `market`: Market share and competitive positioning
- `projections`: Future guidance and projections
- `strategy`: Strategic initiatives
- `costs`: Cost reduction and efficiency
- `other`: Other financial claims

**Rate Limit:** 5 requests per minute

#### `POST /api/ai-agent/compare-claims`

Compare extracted claims against a shareholder letter.

**Request Body:**
```json
{
  "claims": [
    {
      "claim": "Revenue grew by 25%",
      "category": "revenue",
      "confidence": "high"
    }
  ],
  "shareholder_letter": "Dear shareholders, our revenue increased by 23%..."
}
```

**Response:**
```json
{
  "verified_claims": [
    {
      "claim": "Revenue grew by 25%",
      "status": "VERIFIED",
      "evidence": "Shareholder letter confirms 23% growth",
      "discrepancy": "2% difference"
    }
  ],
  "summary": {
    "total_claims": 1,
    "verified": 1,
    "contradicted": 0,
    "unverifiable": 0
  },
  "key_discrepancies": []
}
```

**Verdict Status:**
- `VERIFIED`: Claim matches or is supported by document
- `CONTRADICTED`: Claim contradicts document
- `NOT_FOUND`: Claim cannot be verified from document
- `PARTIAL`: Claim partially matches document

#### `POST /api/ai-agent/verify-youtube-video`

Complete verification workflow for a YouTube video.

**Request Body:**
```json
{
  "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "shareholder_letter": "Optional shareholder letter text..."
}
```

**Response:**
```json
{
  "video_id": "VIDEO_ID",
  "video_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "transcript": "Full transcript...",
  "extracted_claims": [...],
  "verification_results": {
    "verified_claims": [...],
    "summary": {...},
    "key_discrepancies": [...]
  },
  "executive_summary": "Summary of verification results...",
  "recommendations": [
    "Review claim about revenue growth",
    "Verify user metrics independently"
  ],
  "metadata": {
    "analysis_timestamp": "2024-01-24T20:00:00",
    "model_used": "gpt-4o-mini"
  }
}
```

**Workflow:**
1. Extract transcript from YouTube video
2. Extract financial claims from transcript
3. Compare claims with shareholder letter (if provided)
4. Generate comprehensive verification report

**Rate Limit:** 5 requests per minute

#### `POST /api/ai-agent/verify-from-files`

Complete verification workflow from uploaded .txt files.

**Request:** Multipart form data
- `transcript_file`: Required .txt file containing transcript
- `shareholder_letter_file`: Optional .txt file containing shareholder letter

**Response:** Same as `/verify-youtube-video`

**Rate Limit:** 5 requests per minute

#### `GET /api/ai-agent/health`

Check AI Agent service health.

**Response:**
```json
{
  "status": "ok",
  "service": "AI Agent Service",
  "endpoints": [
    "/extract-claims",
    "/compare-claims",
    "/verify-youtube-video",
    "/verify-from-files"
  ],
  "ai_model": "gpt-4o-mini"
}
```

---

### Verification Endpoints

#### `POST /api/verify`

Verify claims from YouTube video against company documents in Tower.

**Request Body:**
```json
{
  "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "company_id": "duolingo"
}
```

**Response:**
```json
{
  "results": [
    {
      "claim": {
        "claim": "Revenue grew by 25%",
        "category": "revenue"
      },
      "verification": {
        "verdict": "VERIFIED",
        "citations": [
          {
            "document_id": "doc-123",
            "page_number": 5,
            "excerpt": "Revenue increased by 25%..."
          }
        ]
      },
      "chunks": [...],
      "document_id": "doc-123"
    }
  ]
}
```

**Workflow:**
1. Extract transcript from YouTube video
2. Extract claims from transcript
3. Retrieve relevant document chunks from Tower for the company
4. Verify each claim against retrieved chunks

---

### Document Management

#### `POST /api/documents`

Upload a document to Tower for processing.

**Request Body:**
```json
{
  "company_id": "duolingo",
  "pdf_url": "https://example.com/document.pdf"
}
```

**Response:**
```json
{
  "document_id": "2ed0288f-0c6c-49f4-841a-1337188b1b2c",
  "status": "completed"
}
```

**Note:** Currently only supports PDF URLs. File upload will be added in future versions.

**Workflow:**
1. Downloads PDF from URL
2. Generates SHA256 hash
3. Stores document metadata in Tower
4. Returns document_id for chunk storage

---

### Company Management

#### `GET /api/companies`

List all companies in the system.

**Response:**
```json
{
  "companies": [
    {
      "company_id": "duolingo",
      "name": "Duolingo",
      "ticker": "DUOL",
      "industry": "Education Technology",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

**Note:** Returns companies that have documents stored in Tower.

---

### Version Comparison

#### `POST /api/version-diff`

Compare two versions of a company document.

**Request Body:**
```json
{
  "company_id": "duolingo",
  "document_id_1": "doc-version-1",
  "document_id_2": "doc-version-2"
}
```

**Response:**
```json
{
  "company_id": "duolingo",
  "document_1": {
    "document_id": "doc-version-1",
    "version": "Q3-2024",
    "created_at": "2024-09-01T00:00:00Z"
  },
  "document_2": {
    "document_id": "doc-version-2",
    "version": "Q4-2024",
    "created_at": "2024-12-01T00:00:00Z"
  },
  "changed_sections": [
    {
      "section": "Revenue",
      "change_type": "modified",
      "old_content": "Revenue: $100M",
      "new_content": "Revenue: $125M",
      "page_number": 5
    }
  ],
  "summary": {
    "total_changes": 1,
    "added_sections": 0,
    "modified_sections": 1,
    "removed_sections": 0
  }
}
```

**Change Types:**
- `added`: New section in document_2
- `modified`: Section changed between versions
- `removed`: Section removed in document_2

---

## Interactive API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`
- **OpenAPI Schema**: `http://127.0.0.1:8000/openapi.json`

---

## Example Usage

### Complete Verification Workflow

```bash
# 1. Extract transcript
curl -X POST "http://127.0.0.1:8000/api/youtube/transcript" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'

# 2. Extract claims
curl -X POST "http://127.0.0.1:8000/api/ai-agent/extract-claims" \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Our revenue grew by 25%..."}'

# 3. Compare with shareholder letter
curl -X POST "http://127.0.0.1:8000/api/ai-agent/compare-claims" \
  -H "Content-Type: application/json" \
  -d '{
    "claims": [...],
    "shareholder_letter": "..."
  }'

# Or use the complete workflow endpoint:
curl -X POST "http://127.0.0.1:8000/api/ai-agent/verify-youtube-video" \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "shareholder_letter": "..."
  }'
```

### Document Management

```bash
# Upload document
curl -X POST "http://127.0.0.1:8000/api/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "duolingo",
    "pdf_url": "https://example.com/document.pdf"
  }'

# List companies
curl "http://127.0.0.1:8000/api/companies"
```

---

## Environment Variables

Required environment variables for full functionality:

- `OPENAI_API_KEY`: OpenAI API key for AI agent services
- `TOWER_API_KEY`: Tower.dev API key for document storage
- `RUNPOD_API_KEY`: RunPod API key for audio transcription
- `RUNPOD_ENDPOINT_ID`: RunPod endpoint ID for Whisper
- `IMAGEKIT_PRIVATE_KEY`: ImageKit private key for temporary file storage
- `IMAGEKIT_URL_ENDPOINT`: ImageKit URL endpoint
- `OPIK_API_KEY`: Opik API key for observability (optional)

See `.env.example` for template.

---

## Notes

- All timestamps are in ISO 8601 format (UTC)
- File uploads are limited to .txt files for transcript and shareholder letter
- PDF processing requires Tower.dev integration
- AI model can be configured in `backend/core/config.json`
