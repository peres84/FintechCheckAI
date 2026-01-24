# Product Requirements Document: Fintech Check AI

## Project Overview

Build a fact-checking platform that verifies claims made in YouTube videos against official company quarterly reports with immutable versioned data storage.

## Technical Stack

- **Backend**: FastAPI (Python 3.11+)
- **Package Manager**: UV (fast Python package installer)
- **Database**: Tower.dev with Apache Iceberg
- **Document Processing**: RunPod + Marker-PDF/DocTR
- **LLM Framework**: LangChain + OpenAI
- **Observability**: Opik
- **MCP Servers**: Context7, Magic, Tower
- **Development**: Codex CLI for agent-assisted development

## Project Structure

```
fintech-check-ai/
├── .codex/
│   └── init.md                 # Codex initialization
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── youtube.py
│   │   │   ├── verification.py
│   │   │   └── documents.py
│   │   └── dependencies.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── logging.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── youtube_service.py
│   │   ├── rag_service.py
│   │   ├── pdf_service.py
│   │   ├── tower_service.py
│   │   └── opik_service.py      # Opik telemetry service
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── claim_extractor.py
│   │   ├── chunk_retriever.py
│   │   └── verification_agent.py
│   ├── etl/
│   │   ├── __init__.py
│   │   ├── pdf_processor.py
│   │   ├── normalizer.py
│   │   ├── chunker.py
│   │   └── pdf_downloader.py
│   ├── tower/
│   │   ├── apps/
│   │   │   ├── document-ingestion/
│   │   │   │   ├── Towerfile
│   │   │   │   └── main.py
│   │   │   ├── chunk-storage/
│   │   │   │   ├── Towerfile
│   │   │   │   └── main.py
│   │   │   └── verification-logs/
│   │   │       ├── Towerfile
│   │   │       └── main.py
│   │   └── schemas/
│   │       ├── companies.sql
│   │       ├── documents.sql
│   │       └── chunks.sql
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py
│   │   └── responses.py
│   ├── main.py                 # FastAPI app entry point
│   └── pyproject.toml          # UV project file
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── test_youtube_api.py
│   │   ├── test_verification_api.py
│   │   └── test_documents_api.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── test_youtube_service.py
│   │   ├── test_rag_service.py
│   │   ├── test_tower_service.py
│   │   └── test_opik_service.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── test_claim_extractor.py
│   │   ├── test_chunk_retriever.py
│   │   └── test_verification_agent.py
│   ├── etl/
│   │   ├── __init__.py
│   │   ├── test_pdf_processor.py
│   │   ├── test_normalizer.py
│   │   └── test_chunker.py
│   ├── tower/
│   │   ├── __init__.py
│   │   ├── test_document_ingestion.py
│   │   ├── test_chunk_storage.py
│   │   └── test_queries.py
│   └── fixtures/
│       ├── sample.pdf
│       └── sample_transcript.json
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── scripts/
│   ├── setup_tower.sh
│   └── seed_duolingo_data.py
├── docs/
│   ├── architecture.md
│   ├── api.md
│   └── deployment.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── pytest.ini
└── README.md
```

## Phases & Tasks

### Phase 0: Setup & Infrastructure

**Tasks:**

- [ ] Initialize UV project with pyproject.toml
- [ ] Set up FastAPI backend skeleton
- [ ] Configure Tower CLI and create initial schemas
- [ ] Set up testing framework (pytest)
- [ ] Configure environment variables and secrets
- [ ] Create Docker setup for local development
- [ ] Initialize Opik workspace for telemetry

**Acceptance Criteria:**

- UV package management working
- FastAPI server runs on `localhost:8000`
- Tower CLI authenticated and team selected
- All tests run with `pytest`
- Opik dashboard accessible

### Phase 1: Document Ingestion (Tower Apps)

**Tasks:**

- [ ] Create `document-ingestion` Tower app
  - Accept PDF binary or URL
  - Generate SHA256 hash
  - Store metadata in Iceberg table
- [ ] Create `chunk-storage` Tower app
  - Receive normalized chunks
  - Store with embeddings
  - Link to document via foreign key
- [ ] Create Iceberg schemas for:
  - `companies` table
  - `documents` table
  - `chunks` table
  - `verifications` table
- [ ] Build tests for each Tower app

**Acceptance Criteria:**

- Can upload PDF and get document_id
- Can store chunks with proper references
- Hash collision detection works
- Tests pass for all CRUD operations

### Phase 2: PDF Processing Pipeline (ETL)

**Tasks:**

- [ ] Implement PDF downloader (SEC EDGAR integration)
- [ ] Set up RunPod GPU instance for OCR
- [ ] Create PDF processor with Marker-PDF
- [ ] Build normalization layer:
  - Whitespace normalization
  - Number/date formatting
  - Section detection
- [ ] Implement deterministic chunker
- [ ] Create embeddings generator (OpenAI)
- [ ] Build re-parsing comparison logic

**Acceptance Criteria:**

- Same PDF produces same chunks on re-parse (95%+ similarity)
- Chunks have page numbers and coordinates
- Embeddings stored in chunks table
- Processing handles errors gracefully

### Phase 3: YouTube Transcript Extraction

**Tasks:**

- [ ] Implement YouTube transcript API integration
- [ ] Create transcript normalizer
- [ ] Build timestamp-to-claim mapper
- [ ] Add caching for transcripts
- [ ] Create FastAPI endpoint `/api/youtube/transcript`

**Acceptance Criteria:**

- Extracts transcript with timestamps
- Handles videos without captions
- Returns structured JSON
- API endpoint tested

### Phase 4: RAG System & Claim Verification

**Tasks:**

- [ ] Build claim extraction agent (LangChain)
  - Extract factual claims from transcript
  - Categorize claims (financial, user metrics, etc.)
- [ ] Implement chunk retriever
  - Hybrid search (semantic + keyword)
  - Return top-k with confidence scores
- [ ] Create verification agent
  - Compare claim against retrieved chunks
  - Generate verdict: VERIFIED/NOT_FOUND/CONTRADICTED
  - Include citations (PDF hash, page, section)
- [ ] **Integrate Opik service for telemetry**
  - Track agent execution traces
  - Log LLM calls and token usage
  - Monitor retrieval performance
  - Create dashboards for debugging
- [ ] Create FastAPI endpoint `/api/verify`

**Acceptance Criteria:**

- Extracts ≥80% of verifiable claims
- Returns proper citations for matches
- "NOT_FOUND" for unverifiable claims
- Opik dashboard shows agent traces with full context
- Can debug failed verifications through Opik

### Phase 5: Backend API

**Tasks:**

- [ ] Create verification endpoint
  - Input: YouTube URL, company_id
  - Output: Claims with verdicts and citations
- [ ] Create document upload endpoint
  - Input: PDF file or URL, company metadata
  - Output: document_id, processing status
- [ ] Create company listing endpoint
- [ ] Add version diff endpoint
  - Compare two document versions
  - Return changed sections
- [ ] Implement rate limiting
- [ ] Add API documentation (OpenAPI/Swagger)
- [ ] Instrument all endpoints with Opik tracking

**Acceptance Criteria:**

- All endpoints return proper status codes
- Error handling for invalid inputs
- API docs accessible at `/docs`
- Tests cover all endpoints
- Opik tracks all API calls

### Phase 6: Frontend Landing Page

**Tasks:**

- [ ] Build simple HTML/JS landing page
- [ ] YouTube URL input field
- [ ] Company dropdown (populated from API)
- [ ] Optional PDF upload
- [ ] Results display:
  - Claims table with verdicts
  - Citations with links
  - Version diff viewer
- [ ] Loading states and error handling

**Acceptance Criteria:**

- Works without JavaScript framework
- Mobile responsive
- Shows clear loading indicators
- Error messages are user-friendly

### Phase 7: Testing & Quality

**Tasks:**

- [ ] Write integration tests for full workflow
- [ ] Create test fixtures (sample PDFs, transcripts)
- [ ] Test edge cases:
  - Invalid YouTube URLs
  - Corrupted PDFs
  - Missing data in Tower
- [ ] Performance testing (100+ chunks)
- [ ] Security testing (input validation)

**Acceptance Criteria:**

- ≥80% code coverage
- All edge cases handled
- Performance: <5s for verification
- No security vulnerabilities

### Phase 8: Deployment & Monitoring

**Tasks:**

- [ ] Set up production Tower workspace
- [ ] Deploy FastAPI to cloud (Railway/Render)
- [ ] Configure Opik production instance
- [ ] Set up RunPod autoscaling
- [ ] Create monitoring dashboards
- [ ] Document deployment process

**Acceptance Criteria:**

- Production environment live
- Monitoring alerts configured
- Deployment documented
- Rollback procedure tested

## Opik Integration Details

### Opik Service (`backend/services/opik_service.py`)

Centralized service for all Opik telemetry:

**Key Features:**

- Track agent execution flows
- Log LLM calls with prompts and responses
- Monitor RAG retrieval performance
- Measure token usage and costs
- Create custom metrics for verification accuracy
- Dashboard for debugging failed verifications

**What Gets Tracked:**

- Claim extraction: Input transcript → Extracted claims
- Chunk retrieval: Query → Retrieved chunks with scores
- Verification: Claim + Chunks → Verdict with reasoning
- LLM calls: Prompts, responses, token counts, latency
- Errors: Full stack traces with context

### Opik Dashboards

- **Agent Performance**: Success rates, latency by agent type
- **LLM Usage**: Token consumption, cost tracking
- **Retrieval Quality**: Chunk relevance scores, hit rates
- **Error Analysis**: Failed verifications with full context

## Non-Functional Requirements

### Performance

- Verification latency: <5 seconds for 10-minute video
- PDF processing: <2 minutes for 50-page document
- API response time: <500ms (95th percentile)

### Scalability

- Support 100+ documents per company
- Handle 1000+ chunks per document
- Process 10 concurrent verifications

### Reliability

- 99.9% uptime for API
- Automatic retry for failed PDF processing
- Graceful degradation if RunPod unavailable

### Security

- API key authentication
- Input validation on all endpoints
- Rate limiting: 10 req/min per IP
- PDF virus scanning before processing

### Observability

- All agent interactions logged to Opik
- API metrics in Prometheus format
- Error tracking with stack traces
- Audit trail for all verifications

## Success Metrics

- **Accuracy**: ≥95% of verifiable claims correctly identified
- **Precision**: ≥90% of "VERIFIED" claims are actually correct
- **User Satisfaction**: Manual review of 20 videos shows accurate results
- **Performance**: Processing time meets SLAs

## Future Enhancements (Post-MVP)

- Support for earnings call audio
- Multi-language support
- Chrome extension for in-video verification
- Automated daily scraping of new filings
- API for third-party integrations
- Advanced diff visualization
- Support for more companies (S&P 500)
