# Backend Tasks - Prioritized Missing Features

This document lists all missing backend tasks in priority order. Focus on backend first, then frontend integration.

## Priority 1: Critical Backend Fixes & Completions

### Task 1.1: Complete PDF Service Implementation
**Status**: ❌ Not Started  
**Priority**: 🔴 Critical  
**Estimated Time**: 4-6 hours

**Description**:  
Implement the PDF processing service that's currently just a placeholder.

**Requirements**:
- [ ] Implement PDF text extraction
- [ ] Integrate with RunPod Marker-PDF/DocTR for OCR
- [ ] Generate chunks from PDF content
- [ ] Extract metadata (title, author, creation date)
- [ ] Handle various PDF formats and edge cases
- [ ] Add error handling for corrupted PDFs
- [ ] Create tests for PDF processing

**Files to Modify**:
- `backend/services/pdf_service.py`
- `backend/etl/pdf_processor.py`
- `tests/services/test_pdf_service.py`

**Dependencies**:
- RunPod endpoint for OCR
- PDF parsing library (PyPDF2, pdfplumber, or similar)

---

### Task 1.2: Implement Semantic Search in RAG Service
**Status**: ❌ Not Started  
**Priority**: 🔴 Critical  
**Estimated Time**: 3-4 hours

**Description**:  
Currently RAG service only uses keyword matching. Need to implement semantic search using embeddings stored in chunks.

**Requirements**:
- [ ] Use embeddings from chunks table for semantic similarity
- [ ] Implement cosine similarity calculation
- [ ] Support hybrid search (semantic + keyword)
- [ ] Add configuration for search method selection
- [ ] Optimize for performance (vector indexing if needed)
- [ ] Update tests to cover semantic search

**Files to Modify**:
- `backend/services/rag_service.py`
- `backend/tower/apps/rag-chunk-query/main.py` (if needed)
- `tests/services/test_rag_service.py`

**Dependencies**:
- Embeddings must be stored in chunks table (already done)
- NumPy or similar for vector operations

---

### Task 1.3: Complete Verification Logs Tower App
**Status**: ❌ Placeholder  
**Priority**: 🟡 High  
**Estimated Time**: 2-3 hours

**Description**:  
The verification-logs Tower app is currently a placeholder. Implement it to store verification results.

**Requirements**:
- [ ] Create handler for verification log storage
- [ ] Store verification results in Tower verifications table
- [ ] Include metadata (video_id, company_id, timestamp)
- [ ] Support querying verification history
- [ ] Add Towerfile configuration
- [ ] Create tests

**Files to Modify**:
- `backend/tower/apps/verification-logs/main.py`
- `backend/tower/apps/verification-logs/Towerfile`
- `tests/tower/test_verification_logs.py`

---

### Task 1.4: Add File Upload Support to Documents Endpoint
**Status**: ⚠️ Partial (only URL support)  
**Priority**: 🟡 High  
**Estimated Time**: 2-3 hours

**Description**:  
Currently `/api/documents` only accepts PDF URLs. Add support for direct file uploads.

**Requirements**:
- [ ] Accept multipart/form-data file uploads
- [ ] Validate file type (PDF only)
- [ ] Validate file size limits
- [ ] Upload to ImageKit or similar storage
- [ ] Process uploaded file through document-ingestion
- [ ] Update API documentation
- [ ] Add tests for file upload

**Files to Modify**:
- `backend/api/routes/documents.py`
- `backend/services/pdf_service.py`
- `docs/api.md`
- `tests/api/test_documents_api.py`

---

## Priority 2: Backend Enhancements

### Task 2.1: Add Caching Layer
**Status**: ❌ Not Started  
**Priority**: 🟡 High  
**Estimated Time**: 3-4 hours

**Description**:  
Add Redis or in-memory caching for frequently accessed data.

**Requirements**:
- [ ] Cache YouTube transcripts (key: video_id)
- [ ] Cache extracted claims (key: transcript hash)
- [ ] Cache retrieved chunks (key: document_id + query)
- [ ] Add cache TTL configuration
- [ ] Implement cache invalidation
- [ ] Add Redis integration (optional, fallback to in-memory)
- [ ] Add cache metrics/monitoring

**Files to Create/Modify**:
- `backend/services/cache_service.py` (new)
- `backend/api/routes/youtube.py`
- `backend/api/routes/ai_agent.py`
- `backend/services/rag_service.py`
- `backend/core/config.json`

**Dependencies**:
- Redis (optional, with in-memory fallback)

---

### Task 2.2: Improve Error Messages and Validation
**Status**: ⚠️ Partial  
**Priority**: 🟡 Medium  
**Estimated Time**: 2-3 hours

**Description**:  
Enhance error messages to be more user-friendly and add better input validation.

**Requirements**:
- [ ] Add Pydantic validators for all request models
- [ ] Improve error messages with actionable guidance
- [ ] Add request validation middleware
- [ ] Validate YouTube URLs more thoroughly
- [ ] Add file size/type validation for uploads
- [ ] Create custom exception classes
- [ ] Update error response format

**Files to Modify**:
- `backend/models/schemas.py`
- `backend/api/middleware/` (new validation middleware)
- `backend/models/responses.py`
- All route files

---

### Task 2.3: Add Batch Processing Support
**Status**: ❌ Not Started  
**Priority**: 🟡 Medium  
**Estimated Time**: 4-5 hours

**Description**:  
Add endpoints to process multiple videos/documents in batch.

**Requirements**:
- [ ] Create batch verification endpoint
- [ ] Support async processing with job IDs
- [ ] Add job status tracking
- [ ] Implement job queue (Celery or similar)
- [ ] Add batch results retrieval
- [ ] Create tests for batch processing

**Files to Create/Modify**:
- `backend/api/routes/batch.py` (new)
- `backend/services/job_service.py` (new)
- `backend/models/schemas.py`
- `tests/api/test_batch_api.py` (new)

**Dependencies**:
- Task queue system (Celery, RQ, or similar)

---

### Task 2.4: Add Authentication & Authorization
**Status**: ❌ Not Started  
**Priority**: 🟡 Medium  
**Estimated Time**: 3-4 hours

**Description**:  
Add API key authentication and user authorization.

**Requirements**:
- [ ] Implement API key authentication
- [ ] Add user roles (admin, user, read-only)
- [ ] Create authentication middleware
- [ ] Add rate limiting per user
- [ ] Store API keys securely (hashed)
- [ ] Add user management endpoints (admin only)
- [ ] Update all endpoints with auth decorators
- [ ] Add tests for authentication

**Files to Create/Modify**:
- `backend/api/middleware/auth.py` (new)
- `backend/core/auth.py` (new)
- `backend/models/schemas.py`
- All route files
- `backend/core/config.json`

---

## Priority 3: Backend Testing & Quality

### Task 3.1: Increase Test Coverage to 80%+
**Status**: ⚠️ Partial (~45% estimated)  
**Priority**: 🟡 Medium  
**Estimated Time**: 6-8 hours

**Description**:  
Increase test coverage across all modules.

**Requirements**:
- [ ] Add integration tests for full workflows
- [ ] Add edge case tests
- [ ] Add error condition tests
- [ ] Mock external services properly
- [ ] Add performance tests
- [ ] Set up coverage reporting
- [ ] Add coverage to CI/CD (future)

**Files to Create/Modify**:
- All test files in `tests/`
- `pytest.ini` (coverage configuration)
- `tests/integration/` (new directory)

---

### Task 3.2: Add Integration Tests
**Status**: ⚠️ Partial  
**Priority**: 🟡 Medium  
**Estimated Time**: 4-5 hours

**Description**:  
Add end-to-end integration tests for complete workflows.

**Requirements**:
- [ ] Test complete verification workflow
- [ ] Test document ingestion workflow
- [ ] Test RAG retrieval workflow
- [ ] Use test fixtures and mocks
- [ ] Test error recovery scenarios
- [ ] Add test data setup/teardown

**Files to Create/Modify**:
- `tests/integration/test_complete_flow.py` (enhance existing)
- `tests/integration/test_document_workflow.py` (new)
- `tests/integration/test_rag_workflow.py` (new)
- `tests/fixtures/` (add more fixtures)

---

### Task 3.3: Add Performance Testing
**Status**: ❌ Not Started  
**Priority**: 🟢 Low  
**Estimated Time**: 3-4 hours

**Description**:  
Add performance benchmarks and load testing.

**Requirements**:
- [ ] Create performance test suite
- [ ] Benchmark API endpoints
- [ ] Test with 100+ chunks
- [ ] Test concurrent requests
- [ ] Identify bottlenecks
- [ ] Add performance monitoring

**Files to Create**:
- `tests/performance/` (new directory)
- `tests/performance/test_api_performance.py` (new)
- `tests/performance/test_rag_performance.py` (new)

---

## Priority 4: Backend Infrastructure

### Task 4.1: Add Database Migrations
**Status**: ❌ Not Started  
**Priority**: 🟡 Medium  
**Estimated Time**: 2-3 hours

**Description**:  
Add migration system for Tower schema changes.

**Requirements**:
- [ ] Create migration system for Tower schemas
- [ ] Version control schema changes
- [ ] Add rollback capability
- [ ] Document migration process

**Files to Create**:
- `backend/tower/migrations/` (new directory)
- Migration scripts

---

### Task 4.2: Add Health Check Endpoints for All Services
**Status**: ⚠️ Partial  
**Priority**: 🟢 Low  
**Estimated Time**: 1-2 hours

**Description**:  
Add health check endpoints for all services.

**Requirements**:
- [ ] Add `/api/rag/health`
- [ ] Add `/api/tower/health`
- [ ] Add `/api/opik/health`
- [ ] Add comprehensive health status
- [ ] Include service dependencies status

**Files to Modify**:
- `backend/api/routes/` (add health endpoints)
- `backend/main.py` (aggregate health check)

---

### Task 4.3: Add Request/Response Logging Middleware
**Status**: ❌ Not Started  
**Priority**: 🟢 Low  
**Estimated Time**: 2-3 hours

**Description**:  
Add middleware to log all requests and responses (with sensitive data redaction).

**Requirements**:
- [ ] Log request method, path, headers
- [ ] Log response status, time taken
- [ ] Redact sensitive data (API keys, tokens)
- [ ] Configurable log level
- [ ] Add request ID tracking

**Files to Create/Modify**:
- `backend/api/middleware/logging.py` (new)
- `backend/main.py`

---

## Priority 5: Documentation & Developer Experience

### Task 5.1: Add API Examples and Tutorials
**Status**: ⚠️ Partial  
**Priority**: 🟢 Low  
**Estimated Time**: 2-3 hours

**Description**:  
Add comprehensive examples and tutorials for API usage.

**Requirements**:
- [ ] Create API usage examples
- [ ] Add code samples in multiple languages
- [ ] Create tutorial for common workflows
- [ ] Add troubleshooting guide

**Files to Create**:
- `docs/examples/` (new directory)
- `docs/tutorials/` (new directory)

---

### Task 5.2: Add OpenAPI Schema Enhancements
**Status**: ⚠️ Basic  
**Priority**: 🟢 Low  
**Estimated Time**: 1-2 hours

**Description**:  
Enhance OpenAPI schema with better descriptions and examples.

**Requirements**:
- [ ] Add detailed descriptions to all endpoints
- [ ] Add request/response examples
- [ ] Add error response schemas
- [ ] Add authentication documentation

**Files to Modify**:
- All route files (add OpenAPI decorators)
- `backend/models/schemas.py`

---

## Task Summary

| Priority | Task Count | Estimated Time |
|----------|------------|----------------|
| Priority 1 (Critical) | 4 tasks | 11-16 hours |
| Priority 2 (High) | 4 tasks | 12-16 hours |
| Priority 3 (Medium) | 3 tasks | 13-17 hours |
| Priority 4 (Infrastructure) | 3 tasks | 5-8 hours |
| Priority 5 (Documentation) | 2 tasks | 3-5 hours |
| **Total** | **16 tasks** | **44-62 hours** |

---

## Next Steps

1. **Start with Priority 1 tasks** - These are critical for core functionality
2. **Complete one task at a time** - Don't start multiple tasks simultaneously
3. **Write tests as you go** - Don't leave testing for later
4. **Update documentation** - Keep docs in sync with code changes
5. **Commit frequently** - Small, focused commits

---

## Notes

- All time estimates are rough and may vary
- Some tasks may have dependencies on external services
- Prioritize based on current project needs
- Frontend integration tasks will be added separately

---

*Last Updated: 2026-01-25*
