# Backend Services

This directory contains service modules that handle external integrations and core business logic for the application.

## Services Overview

### `youtube_service.py`

**Purpose**: Extracts transcripts from YouTube videos using multiple fallback methods.

**Main Function**: `fetch_transcript(video_url: str) -> Dict[str, Any]`

**Workflow**:
1. **YouTube Captions First**: Attempts to extract transcript directly from YouTube's built-in captions/subtitles
2. **Audio Transcription Fallback**: If captions aren't available, downloads the audio and transcribes it using AI

**Detailed Process**:

#### Method 1: YouTube Captions
- Uses `youtube-transcript-api` to fetch existing captions
- Fast and accurate when available
- Returns immediately if successful

#### Method 2: Audio Transcription Pipeline
When captions aren't available, the service:

1. **Download Audio**: Uses `yt-dlp` to download audio-only stream
2. **Convert Format**: Uses FFmpeg to convert to 16kHz mono WAV format optimized for speech recognition
3. **Upload to ImageKit**: Temporarily uploads WAV file to get a public URL
4. **Transcribe with RunPod**: Sends audio URL to RunPod Whisper endpoint for AI transcription
5. **Cleanup**: Deletes the temporary WAV file from ImageKit
6. **Return Results**: Returns transcript with metadata

**Dependencies**:
- `yt-dlp`: YouTube audio downloading
- `youtube-transcript-api`: Caption extraction
- `runpod`: AI transcription service
- `requests`: HTTP requests for ImageKit
- `ffmpeg`: Audio format conversion (system dependency)

**Environment Variables Required**:
- `RUNPOD_API_KEY`: API key for RunPod service
- `RUNPOD_ENDPOINT_ID`: Specific endpoint ID for Whisper transcription
- `IMAGEKIT_PRIVATE_KEY`: Private key for ImageKit file storage
- `IMAGEKIT_URL_ENDPOINT`: ImageKit URL endpoint

**Return Format**:
```python
{
    "transcript": "Full transcript text...",
    "source": "youtube_captions" | "audio_transcription",
    "video_id": "YouTube video ID",
    "status": "completed" | "failed",
    "duration": 123.45,  # Only for audio transcription
    "language": "en"     # Only for audio transcription
}
```

**Error Handling**:
- Validates environment variables on startup
- Handles YouTube API errors gracefully
- Provides detailed error messages for debugging
- Automatically cleans up temporary files even on failure

**Usage Example**:
```python
from backend.services.youtube_service import fetch_transcript

# Get transcript from any YouTube video
result = await fetch_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
print(result["transcript"])
```

**Performance Notes**:
- YouTube captions: ~1-2 seconds
- Audio transcription: ~30-60 seconds depending on video length
- Temporary files are automatically cleaned up
- Uses async/await for non-blocking operations

---

### `ai_agent_service.py`

**Purpose**: AI-powered analysis and comparison of financial documents and transcripts.

**Main Class**: `AIAgentService`

**Key Methods**:
- `extract_claims_from_transcript(transcript: str) -> List[Dict]`: Extract financial claims
- `compare_with_shareholder_letter(claims: List[Dict], letter: str) -> Dict`: Compare claims
- `generate_verification_report(...) -> Dict`: Generate comprehensive reports

**AI Model**: Configurable via `config.json` (default: `gpt-4o-mini`)

**Features**:
- Extracts claims with categorization (revenue, profit, users, etc.)
- Identifies numerical values and context
- Compares claims against official documents
- Generates verification reports with recommendations

**Environment Variables Required**:
- `OPENAI_API_KEY`: OpenAI API key

**Configuration**:
- Model selection in `backend/core/config.json`
- Token limits and temperature settings

**Usage Example**:
```python
from backend.services.ai_agent_service import ai_agent_service

# Extract claims
claims = await ai_agent_service.extract_claims_from_transcript(transcript)

# Compare with document
result = await ai_agent_service.compare_with_shareholder_letter(claims, letter_text)
```

**Error Handling**:
- Validates API key on initialization
- Handles OpenAI API errors gracefully
- Provides detailed error messages

---

### `rag_service.py`

**Purpose**: Retrieve relevant document chunks using RAG (Retrieval-Augmented Generation).

**Main Function**: `retrieve_chunks_from_tower(document_id: str, query: str, top_k: int = 5) -> List[Dict]`

**Features**:
- Integrates with Tower `rag-chunk-query` app
- Supports keyword-based search
- Returns top-k chunks with relevance scores
- Falls back to simple keyword matching if Tower unavailable

**Workflow**:
1. Query Tower rag-chunk-query app
2. Filter chunks by document_id
3. Score chunks by relevance
4. Return top-k results

**Dependencies**:
- Tower SDK for app execution
- Tower chunk store for reading chunks

**Configuration**:
- Tower catalog and namespace from `config.json`
- Top-k parameter configurable

**Usage Example**:
```python
from backend.services.rag_service import retrieve_chunks_from_tower

# Retrieve relevant chunks
chunks = retrieve_chunks_from_tower(
    document_id="doc-123",
    query="revenue growth",
    top_k=5
)
```

**Future Enhancements**:
- Semantic search using embeddings
- Hybrid search (semantic + keyword)
- Better relevance scoring

---

### `tower_service.py`

**Purpose**: Interface with Tower.dev apps and Iceberg tables.

**Main Class**: `TowerService`

**Key Methods**:
- `call_document_ingestion(...) -> Dict`: Store document metadata
- `call_chunk_storage(...) -> Dict`: Store document chunks
- `get_documents_by_company(company_id: str) -> List[Dict]`: Query documents
- `get_chunks_by_document(document_id: str) -> List[Dict]`: Query chunks
- `execute_sql(sql: str, params: Dict) -> Any`: Execute SQL queries

**Tower Apps Integration**:
- `document-ingestion`: Store document metadata with SHA256 hash
- `chunk-storage`: Store chunks with embeddings
- `rag-chunk-query`: Query chunks using RAG

**Tables Managed**:
- `documents`: Document metadata
- `chunks`: Document chunks
- `companies`: Company information
- `verifications`: Verification logs (future)

**Environment Variables Required**:
- `TOWER_API_KEY`: Tower.dev API key

**Configuration**:
- Catalog and namespace from `config.json`

**Usage Example**:
```python
from backend.services.tower_service import TowerService

tower_service = TowerService()

# Upload document
result = tower_service.call_document_ingestion(
    pdf_url="https://example.com/doc.pdf",
    company_id="duolingo",
    version="v1"
)

# Get documents for company
documents = tower_service.get_documents_by_company("duolingo")
```

**Error Handling**:
- Validates Tower SDK availability
- Handles Tower API errors
- Provides detailed error messages

---

### `opik_service.py`

**Purpose**: Observability and telemetry tracking for agent execution.

**Main Class**: `OpikService`

**Key Methods**:
- `track_claim_extraction(...) -> Dict`: Track claim extraction events
- `track_chunk_retrieval(...) -> Dict`: Track chunk retrieval events
- `track_verification(...) -> Dict`: Track verification events
- `track_llm_call(...) -> Dict`: Track LLM API calls

**Features**:
- Tracks agent execution traces
- Logs LLM calls with prompts and responses
- Monitors retrieval performance
- Measures token usage and costs
- Creates custom metrics for verification accuracy

**Environment Variables Required**:
- `OPIK_API_KEY`: Opik API key (optional)
- `OPIK_WORKSPACE`: Opik workspace name (optional)

**Graceful Degradation**:
- Works without Opik SDK installed
- Runs in no-op mode if API key not set
- Doesn't break application if Opik unavailable

**Usage Example**:
```python
from backend.services.opik_service import get_opik_service

opik_service = get_opik_service()

# Track claim extraction
opik_service.track_claim_extraction(
    transcript=transcript,
    claims=claims,
    metadata={"endpoint": "/extract-claims"}
)
```

**Dashboard**: Access Opik dashboard for agent traces and metrics

---

### `pdf_service.py`

**Status**: ⚠️ Placeholder - Not yet implemented

**Future Purpose**: PDF processing and text extraction

**Planned Features**:
- PDF parsing and text extraction
- Chunk generation from PDFs
- Metadata extraction
- Integration with RunPod for OCR

**Dependencies** (planned):
- PDF parsing library (PyPDF2, pdfplumber, etc.)
- OCR service (RunPod Marker-PDF/DocTR)

---

## Service Patterns

### Common Patterns

All services follow these patterns:

1. **Lazy Initialization**: Clients initialized on first use
2. **Error Handling**: Comprehensive try-catch blocks
3. **Logging**: Structured logging with context
4. **Environment Validation**: Check required env vars
5. **Graceful Degradation**: Work without optional dependencies

### Adding New Services

When adding new service modules:

1. **Create Service File**: `backend/services/{service_name}_service.py`
2. **Follow Naming Convention**: Use descriptive function/class names
3. **Add Error Handling**: Comprehensive error handling
4. **Environment Variables**: Document required env vars
5. **Update This README**: Add service documentation
6. **Create Tests**: Add tests in `tests/services/test_{service_name}.py`
7. **Add Logging**: Use `backend.core.logging.log_handler`

### Service Dependencies

```
youtube_service
  └─> RunPod, ImageKit

ai_agent_service
  └─> OpenAI

rag_service
  └─> tower_service
      └─> Tower SDK

tower_service
  └─> Tower SDK

opik_service
  └─> Opik SDK (optional)

pdf_service
  └─> (Not implemented)
```

---

## Testing

Each service should have a corresponding test file in `tests/services/test_{service_name}.py` that covers:

- **Happy Path Scenarios**: Normal operation
- **Error Conditions**: Invalid inputs, API failures
- **Environment Variable Validation**: Missing keys
- **Integration with External Services**: Mock external APIs
- **Edge Cases**: Empty inputs, null values

**Test Structure**:
```python
import pytest
from backend.services.{service_name}_service import ServiceClass

class TestServiceClass:
    def test_happy_path(self):
        # Test normal operation
        pass
    
    def test_error_handling(self):
        # Test error scenarios
        pass
    
    def test_missing_env_vars(self):
        # Test missing environment variables
        pass
```

**Run Tests**:
```bash
# Run all service tests
pytest tests/services/

# Run specific service test
pytest tests/services/test_youtube_service.py

# Run with coverage
pytest --cov=backend.services tests/services/
```

---

## Performance Considerations

### YouTube Service
- Caching transcripts (future enhancement)
- Async operations for non-blocking I/O

### AI Agent Service
- Token usage optimization
- Model selection based on task complexity
- Rate limiting to prevent API quota exhaustion

### RAG Service
- Caching retrieved chunks (future)
- Batch queries for multiple claims
- Semantic search optimization (future)

### Tower Service
- Connection pooling (if supported)
- Batch operations for multiple documents
- Query optimization

---

## Related Documentation

- **API Endpoints**: `BACKEND_README.md`
- **Architecture**: `docs/architecture.md`
- **Tower Integration**: `docs/TOWER_RUNBOOK.md`
- **Deployment**: `docs/deployment.md`

---

*Last Updated: 2026-01-25*
