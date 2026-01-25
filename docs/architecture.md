# System Architecture

Complete architecture documentation for FinTech Check AI platform.

## Overview

FinTech Check AI is a fact-checking platform that verifies claims made in YouTube videos against official company quarterly reports. The system uses AI agents, RAG (Retrieval-Augmented Generation), and immutable versioned storage.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Frontend   │  │  API Clients │  │  Mobile Apps  │        │
│  │  (React/TS)  │  │   (Future)   │  │   (Future)   │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
└─────────┼─────────────────┼─────────────────┼────────────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                           │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              FastAPI Backend (Python 3.11+)              │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │ │
│  │  │ YouTube  │  │   AI     │  │Document  │  │Company   │ │ │
│  │  │  Routes  │  │  Agent   │  │  Routes  │  │  Routes  │ │ │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │ │
│  └───────┼─────────────┼──────────────┼─────────────┼───────┘ │
└──────────┼─────────────┼──────────────┼─────────────┼─────────┘
           │             │              │             │
           ▼             ▼              ▼             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   YouTube    │  │  AI Agent    │  │     RAG      │        │
│  │   Service    │  │   Service    │  │   Service    │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                 │                  │                 │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐        │
│  │    PDF       │  │    Tower     │  │    Opik      │        │
│  │   Service    │  │   Service    │  │   Service    │        │
│  └──────────────┘  └──────┬───────┘  └──────────────┘        │
└────────────────────────────┼───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT LAYER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │    Claim     │  │    Chunk     │  │ Verification │        │
│  │  Extractor   │  │  Retriever   │  │    Agent     │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
└─────────┼─────────────────┼─────────────────┼────────────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   OpenAI     │  │   RunPod     │  │  ImageKit    │        │
│  │   (GPT-4)    │  │  (Whisper)   │  │  (Storage)   │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Tower.dev + Apache Iceberg                  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐            │   │
│  │  │Documents │  │  Chunks   │  │Companies │            │   │
│  │  │  Table   │  │  Table   │  │  Table   │            │   │
│  │  └──────────┘  └──────────┘  └──────────┘            │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend Layer

**Technology:** React + TypeScript + Vite

**Components:**
- Landing page with hero section
- Analyze page for content input
- Results page with verification display
- Follow-up chat interface
- Theme support (dark/light mode)

**Location:** `frontend/`

**API Integration:** `frontend/src/services/api.ts`

---

### 2. API Gateway Layer

**Technology:** FastAPI (Python 3.11+)

**Responsibilities:**
- Request routing and validation
- Rate limiting
- Error handling
- Response formatting
- API documentation (OpenAPI/Swagger)

**Main Entry Point:** `backend/main.py`

**Route Modules:**
- `backend/api/routes/youtube.py` - YouTube transcript extraction
- `backend/api/routes/ai_agent.py` - AI agent endpoints
- `backend/api/routes/verification.py` - Verification workflow
- `backend/api/routes/documents.py` - Document management
- `backend/api/routes/companies.py` - Company listing
- `backend/api/routes/version_diff.py` - Version comparison

**Middleware:**
- Rate limiting: `backend/api/middleware/rate_limit.py`
- CORS (if needed)
- Request logging

---

### 3. Service Layer

#### YouTube Service
**File:** `backend/services/youtube_service.py`

**Responsibilities:**
- Extract transcripts from YouTube videos
- Fallback to audio transcription via RunPod
- Handle various YouTube URL formats

**Workflow:**
1. Try YouTube captions API first (fast)
2. If unavailable, download audio
3. Convert to WAV format
4. Upload to ImageKit
5. Transcribe via RunPod Whisper
6. Clean up temporary files

#### AI Agent Service
**File:** `backend/services/ai_agent_service.py`

**Responsibilities:**
- Extract financial claims from transcripts
- Compare claims with documents
- Generate verification reports

**AI Model:** Configurable (default: `gpt-4o-mini`)

**Methods:**
- `extract_claims_from_transcript()` - Extract claims
- `compare_with_shareholder_letter()` - Verify claims
- `generate_verification_report()` - Create reports

#### RAG Service
**File:** `backend/services/rag_service.py`

**Responsibilities:**
- Retrieve relevant document chunks
- Query Tower storage
- Support multiple search methods: keyword, semantic, and hybrid

**Search Methods:**
- **Keyword Search**: Token-based matching (fast, no embeddings required)
- **Semantic Search**: Cosine similarity on embeddings (requires OpenAI API)
- **Hybrid Search**: Combines semantic and keyword scores (default, best accuracy)

**Integration:**
- Uses Tower `rag-chunk-query` app
- Generates query embeddings using OpenAI `text-embedding-3-small`
- Returns top-k chunks with relevance scores
- Configurable search method and weights via `config.json`

#### Tower Service
**File:** `backend/services/tower_service.py`

**Responsibilities:**
- Interface with Tower.dev apps
- Execute SQL queries on Iceberg tables
- Manage document and chunk storage

**Tower Apps:**
- `document-ingestion` - Store document metadata
- `chunk-storage` - Store document chunks
- `rag-chunk-query` - Query chunks with RAG

#### PDF Service
**File:** `backend/services/pdf_service.py`

**Status:** ✅ Implemented

**Responsibilities:**
- PDF processing from URLs and local paths
- PDF processing from bytes (file uploads)
- SHA256 hash calculation for document integrity
- Metadata extraction (title, author, creation date, page count)
- Text extraction and normalization
- Chunk generation from extracted text
- Temporary file management and cleanup

**Dependencies:**
- PyMuPDF (fitz) for PDF processing
- RapidOCR for OCR (optional)
- Requests for URL downloads

#### Opik Service
**File:** `backend/services/opik_service.py`

**Responsibilities:**
- Track agent execution traces
- Log LLM calls and token usage
- Monitor retrieval performance
- Create observability dashboards

**Tracking:**
- Claim extraction events
- Chunk retrieval events
- Verification events
- LLM API calls

---

### 4. Agent Layer

#### Claim Extractor
**File:** `backend/agents/claim_extractor.py`

**Responsibilities:**
- Extract financial claims from transcripts
- Categorize claims (revenue, profit, users, etc.)
- Identify numerical values and context

**Uses:** AI Agent Service

#### Chunk Retriever
**File:** `backend/agents/chunk_retriever.py`

**Responsibilities:**
- Retrieve relevant chunks from Tower
- Use RAG service for semantic/keyword search
- Filter by document_id and company_id

**Uses:** RAG Service, Tower Service

#### Verification Agent
**File:** `backend/agents/verification_agent.py`

**Responsibilities:**
- Verify claims against retrieved chunks
- Generate verdicts (VERIFIED/CONTRADICTED/NOT_FOUND)
- Provide citations and evidence

**Uses:** AI Agent Service, Chunk Retriever

---

### 5. ETL Layer

**Location:** `backend/etl/`

**Components:**
- `pdf_downloader.py` ✅ - Download PDFs from URLs
- `pdf_processor.py` ✅ - Process PDF files (PyMuPDF + RapidOCR)
- `normalizer.py` ✅ - Normalize text content
- `chunker.py` ✅ - Split documents into chunks

**Status:** ✅ Implemented

---

### 6. Tower Apps

**Location:** `backend/tower/apps/`

#### Document Ingestion App
**App:** `document-ingestion/`

**Responsibilities:**
- Accept PDF URL or local path
- Generate SHA256 hash
- Store document metadata in Tower

**Tables:** `documents`

#### Chunk Storage App
**App:** `chunk-storage/`

**Responsibilities:**
- Load chunks from JSON (path or URL)
- Store chunks with embeddings
- Link chunks to documents

**Tables:** `chunks`

#### RAG Chunk Query App
**App:** `rag-chunk-query/`

**Responsibilities:**
- Query chunks using RAG
- Return top-k relevant chunks
- Support keyword and semantic search

**Tables:** `chunks`

#### Verification Logs App
**App:** `verification-logs/`

**Status:** ✅ Implemented

**Responsibilities:**
- Store verification results in Tower
- Track YouTube URLs and company IDs
- Record verification verdicts
- Provide audit trail for verifications

**Tables:** `verifications`

**Methods:**
- `call_verification_logs()` - Store verification result
- `get_verifications_by_company()` - Query by company
- `get_verifications_by_url()` - Query by YouTube URL

---

### 7. Data Storage

#### Tower.dev + Apache Iceberg

**Catalog:** `database_catalog` (configurable)
**Namespace:** `default` (configurable)

**Tables:**

1. **companies**
   - `company_id` (string)
   - `name` (string)
   - `ticker` (string, optional)
   - `industry` (string, optional)
   - `created_at` (timestamp)

2. **documents**
   - `document_id` (UUID)
   - `company_id` (string)
   - `version` (string)
   - `sha256` (string) - Immutable hash
   - `source_url` (string)
   - `created_at` (timestamp)

3. **chunks**
   - `chunk_id` (UUID)
   - `document_id` (UUID)
   - `page_number` (integer)
   - `content` (string)
   - `embedding` (array, optional)
   - `created_at` (timestamp)

4. **verifications**
   - `verification_id` (UUID)
   - `video_id` (string)
   - `company_id` (string)
   - `claims` (JSON)
   - `results` (JSON)
   - `created_at` (timestamp)

**Schema Files:** `backend/tower/schemas/*.sql`

---

## Data Flow

### Verification Workflow

```
1. User submits YouTube URL
   │
   ▼
2. YouTube Service extracts transcript
   ├─> Try YouTube captions (fast)
   └─> Fallback: RunPod Whisper (slow)
   │
   ▼
3. AI Agent Service extracts claims
   ├─> OpenAI GPT-4
   └─> Opik tracking
   │
   ▼
4. RAG Service retrieves relevant chunks
   ├─> Query Tower rag-chunk-query app
   └─> Filter by company_id
   │
   ▼
5. Verification Agent verifies claims
   ├─> Compare claims vs chunks
   ├─> Generate verdicts
   └─> Opik tracking
   │
   ▼
6. Return verification results
   └─> Claims with verdicts and citations
```

### Document Ingestion Workflow

```
1. User uploads PDF URL
   │
   ▼
2. Document Ingestion App
   ├─> Download PDF
   ├─> Generate SHA256 hash
   └─> Store in Tower documents table
   │
   ▼
3. Parse PDF into chunks (future)
   ├─> PDF Processor
   ├─> Normalizer
   └─> Chunker
   │
   ▼
4. Chunk Storage App
   ├─> Generate embeddings (future)
   └─> Store in Tower chunks table
   │
   ▼
5. Document ready for verification
```

---

## Technology Stack

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Package Manager:** UV
- **Database:** Tower.dev + Apache Iceberg
- **AI/ML:** OpenAI GPT-4, LangChain
- **Observability:** Opik
- **Audio Transcription:** RunPod Whisper
- **File Storage:** ImageKit

### Frontend
- **Framework:** React 18+
- **Language:** TypeScript
- **Build Tool:** Vite
- **UI Library:** shadcn/ui
- **Styling:** Tailwind CSS

### Infrastructure
- **Containerization:** Docker
- **Orchestration:** docker-compose
- **CI/CD:** TBD

---

## Configuration

### Backend Configuration
**File:** `backend/core/config.json`

**Sections:**
- `network`: Server host, port, workers
- `openai`: AI model selection
- `tower`: Catalog and namespace
- `logging`: Log levels and file locations
- `endpoints`: Rate limiting configuration

### Environment Variables
**File:** `.env`

See `docs/api.md` for complete list.

---

## Security Considerations

1. **API Keys:** Stored in environment variables
2. **Rate Limiting:** Prevents abuse
3. **Input Validation:** Pydantic models validate all inputs
4. **Error Handling:** No sensitive data in error messages
5. **File Uploads:** Limited to .txt files, size limits (future)

---

## Scalability

### Current Limitations
- Single FastAPI instance
- Synchronous processing
- No caching layer

### Future Improvements
- Horizontal scaling with multiple workers
- Async task queue (Celery/RQ)
- Redis caching for transcripts
- CDN for static assets
- Load balancer for API

---

## Monitoring & Observability

### Opik Integration
- Agent execution traces
- LLM call tracking
- Performance metrics
- Error tracking

### Logging
- Structured logging to files
- Console output
- Log rotation
- Different log levels per environment

### Health Checks
- `/health` - Overall API health
- `/api/youtube/health` - YouTube service
- `/api/ai-agent/health` - AI Agent service

---

## Future Enhancements

1. ✅ **Semantic Search:** Use embeddings for better chunk retrieval - **COMPLETED**
2. ✅ **PDF Processing:** Complete ETL pipeline - **COMPLETED**
3. **Caching:** Redis for transcripts and claims
4. **Authentication:** API key management
5. **Webhooks:** Notifications for completed verifications
6. **Batch Processing:** Process multiple videos
7. **Multi-language:** Support non-English transcripts
8. **Vector Indexing:** Optimize semantic search with vector databases (e.g., Pinecone, Weaviate)

---

*Last Updated: 2026-01-25*
