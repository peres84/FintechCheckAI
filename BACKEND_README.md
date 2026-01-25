# FinTech Check AI Backend

A FastAPI-based backend service for AI-powered financial document verification and YouTube transcript extraction.

## Quick Start

### 1. Install Dependencies

#### Using UV (Recommended)
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Unix/Mac

pip install uv
uv pip install -e ./backend
```

#### Using pip
```bash
pip install -r backend/requirements.txt
```

### 2. Environment Setup

Create a `.env` file in the project root:

```env
# OpenAI (Required for AI Agent)
OPENAI_API_KEY=sk-...

# Tower.dev (Required for document storage)
TOWER_API_KEY=...

# RunPod (Required for audio transcription fallback)
RUNPOD_API_KEY=...
RUNPOD_ENDPOINT_ID=...

# ImageKit (Required for temporary file storage)
IMAGEKIT_PRIVATE_KEY=...
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/your-id

# Opik (Optional - for observability)
OPIK_API_KEY=...
OPIK_WORKSPACE=fintech-check-ai

# Server Configuration (Optional)
PORT=8000
APP_ENV=development
```

### 3. Start the Server

#### Option 1: Using the startup script (Recommended)
```bash
python run_server.py
```

#### Option 2: Using the main module directly
```bash
python -m backend.main
```

#### Option 3: Using uvicorn directly
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Option 4: Using batch/shell scripts
```bash
# Windows
start_server.bat

# Unix/Mac
chmod +x start_server.sh
./start_server.sh
```

### 4. Access the API

- **API Documentation (Swagger)**: http://127.0.0.1:8000/docs
- **API Documentation (ReDoc)**: http://127.0.0.1:8000/redoc
- **OpenAPI Schema**: http://127.0.0.1:8000/openapi.json
- **Health Check**: http://127.0.0.1:8000/health

---

## API Endpoints

### Health Check

#### `GET /health`
Returns the overall service health status.

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

**Features:**
- Attempts to extract transcript from YouTube captions first (fast)
- Falls back to audio download and AI transcription if captions unavailable (slower)
- Supports various YouTube URL formats
- Comprehensive error handling and logging

**Rate Limit:** 10 requests per minute

#### `GET /api/youtube/health`
Returns the YouTube service health status and available endpoints.

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

**Rate Limit:** 5 requests per minute

#### `POST /api/ai-agent/compare-claims`
Compare extracted claims against a shareholder letter.

**Request Body:**
```json
{
  "claims": [...],
  "shareholder_letter": "Dear shareholders, our revenue increased by 23%..."
}
```

**Response:**
```json
{
  "verified_claims": [...],
  "summary": {
    "total_claims": 1,
    "verified": 1,
    "contradicted": 0
  },
  "key_discrepancies": []
}
```

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
  "verification_results": {...},
  "executive_summary": "Summary...",
  "recommendations": [...],
  "metadata": {...}
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
      "claim": {...},
      "verification": {
        "verdict": "VERIFIED",
        "citations": [...]
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
  "document_1": {...},
  "document_2": {...},
  "changed_sections": [...],
  "summary": {
    "total_changes": 1,
    "added_sections": 0,
    "modified_sections": 1,
    "removed_sections": 0
  }
}
```

---

## Testing

Run the endpoint tests to verify everything is working:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/api/test_youtube_api.py

# Run with coverage
pytest --cov=backend tests/
```

Test files are located in `tests/` directory:
- `tests/api/` - API endpoint tests
- `tests/services/` - Service tests
- `tests/agents/` - Agent tests
- `tests/etl/` - ETL tests
- `tests/tower/` - Tower app tests

---

## Configuration

The backend configuration is stored in `backend/core/config.json`:

**Network Settings:**
- `host`: Server host (default: 127.0.0.1)
- `server_port`: Server port (default: 8000)
- `reload`: Enable auto-reload (default: true)
- `workers`: Number of workers (default: 1)

**OpenAI Settings:**
- `default_model`: Default AI model (default: gpt-4o-mini)
- `available_models`: List of available models

**Tower Settings:**
- `catalog`: Tower catalog name (default: database_catalog)
- `namespace`: Tower namespace (default: default)

**Logging Settings:**
- `logging_level`: Log level (DEBUG, INFO, WARNING, ERROR)
- `dir_name`: Log directory name
- `log_file_name`: Log file name prefix

**Endpoint Settings:**
- Rate limits per endpoint group
- Endpoint prefixes and routes

---

## Architecture

```
backend/
├── main.py                 # FastAPI application and startup
├── core/
│   ├── config.py          # Configuration loader
│   ├── config.json        # Configuration settings
│   └── logging.py         # Logging setup
├── api/
│   ├── middleware/
│   │   └── rate_limit.py  # Rate limiting middleware
│   └── routes/
│       ├── youtube.py     # YouTube transcript endpoints
│       ├── ai_agent.py    # AI agent endpoints
│       ├── verification.py # Verification endpoints
│       ├── documents.py   # Document management endpoints
│       ├── companies.py  # Company listing endpoints
│       └── version_diff.py # Version comparison endpoints
├── services/
│   ├── youtube_service.py # YouTube transcript service
│   ├── ai_agent_service.py # AI agent service
│   ├── rag_service.py     # RAG retrieval service
│   ├── tower_service.py   # Tower.dev integration
│   ├── opik_service.py    # Opik observability
│   └── pdf_service.py     # PDF processing (placeholder)
├── agents/
│   ├── claim_extractor.py # Claim extraction agent
│   ├── chunk_retriever.py # Chunk retrieval agent
│   └── verification_agent.py # Verification agent
├── etl/
│   ├── pdf_downloader.py  # PDF download
│   ├── pdf_processor.py   # PDF processing
│   ├── normalizer.py      # Text normalization
│   └── chunker.py         # Document chunking
├── tower/
│   ├── apps/              # Tower apps
│   │   ├── document-ingestion/
│   │   ├── chunk-storage/
│   │   ├── rag-chunk-query/
│   │   └── verification-logs/
│   └── schemas/           # Iceberg table schemas
└── models/
    ├── schemas.py         # Pydantic models
    └── responses.py       # Response models
```

---

## Logging

Logs are written to both console and files in the `logs/` directory:
- **File location**: `logs/fintech_check_ai_YYYY-MM-DDTHH-MM-SS.log`
- **Log levels**: DEBUG, INFO, WARNING, ERROR
- **Structured logging**: Timestamps, log levels, and detailed messages

View logs:
```bash
# Tail logs
tail -f logs/fintech_check_ai_*.log

# Windows PowerShell
Get-Content logs\fintech_check_ai_*.log -Wait
```

---

## Error Handling

The API provides comprehensive error handling:

- **400 Bad Request**: Invalid request parameters
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server-side errors, missing environment variables
- **Detailed error messages**: Logged for debugging and returned to clients

All errors follow this format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Development

### Adding New Endpoints

1. Create route file in `backend/api/routes/`
2. Add endpoint configuration to `backend/core/config.json` (for rate limiting)
3. Import and include router in `backend/main.py`
4. Add request/response models to `backend/models/schemas.py`
5. Create tests in `tests/api/`

### Environment Variables

**Required for full functionality:**
- `OPENAI_API_KEY`: For AI agent services
- `TOWER_API_KEY`: For Tower.dev document storage
- `RUNPOD_API_KEY`: For AI audio transcription
- `RUNPOD_ENDPOINT_ID`: RunPod endpoint identifier
- `IMAGEKIT_PRIVATE_KEY`: For temporary file storage
- `IMAGEKIT_URL_ENDPOINT`: ImageKit endpoint URL

**Optional:**
- `OPIK_API_KEY`: For observability tracking
- `OPIK_WORKSPACE`: Opik workspace name
- `PORT`: Server port (default: 8000)
- `APP_ENV`: Environment name (development/production)

---

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the project root directory and virtual environment is activated

2. **Missing Dependencies**: 
   ```bash
   uv pip install -e ./backend
   # or
   pip install -r backend/requirements.txt
   ```

3. **Environment Variables**: Check `.env` file exists in project root and contains required variables

4. **Port Conflicts**: Change port in `config.json` or set `PORT` environment variable

5. **Tower Connection Issues**: 
   - Verify `TOWER_API_KEY` is set
   - Run `tower login` to authenticate
   - Check Tower workspace is accessible

6. **OpenAI API Errors**: 
   - Verify `OPENAI_API_KEY` is valid
   - Check API quota and billing
   - Verify model name in config.json

### Debug Mode

Enable debug logging in `backend/core/config.json`:
```json
{
  "logging": {
    "logging_level": "debug"
  }
}
```

### Getting Help

1. Check logs in `logs/` directory
2. Review error messages in API responses
3. Check Opik dashboard for agent traces (if configured)
4. Review API documentation at `/docs`
5. See `docs/` directory for detailed documentation

---

## Related Documentation

- **API Reference**: `docs/api.md`
- **Architecture**: `docs/architecture.md`
- **Deployment**: `docs/deployment.md`
- **Tower Runbook**: `docs/TOWER_RUNBOOK.md`
- **Services**: `backend/services/README.md`

---

*Last Updated: 2026-01-25*
