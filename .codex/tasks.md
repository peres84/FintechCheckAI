# Development Tasks - Fintech Check AI

## Phase 0: Setup & Infrastructure

### Task 0.1: Initialize Project Structure

**Priority**: P0  
**Estimated Time**: 30 minutes  
**Dependencies**: None

**Steps:**

```bash
mkdir -p youtube-fact-checker/{backend/app/{api,core,services,models},tower/{apps,schemas},agents,etl,tests/{tower,backend,agents,etl},frontend,scripts,docs,.codex}
cd youtube-fact-checker
```

**Validation:**

- [ ] Directory structure matches PRD
- [ ] All folders created

---

### Task 0.2: Configure Codex CLI with MCP Servers

**Priority**: P0  
**Estimated Time**: 15 minutes  
**Dependencies**: Task 0.1

**Steps:**

1. Copy the Codex init file to `.codex/init.md`
2. Verify MCP server access:
   ```bash
   codex: List all available Tower tools
   codex: Query Context7 for FastAPI documentation
   codex: Test Magic component builder availability
   ```

**Validation:**

- [ ] All three MCP servers responding
- [ ] `tower_apps_list` command works
- [ ] Context7 can query docs
- [ ] Magic tools accessible

**Test Command:**

```bash
codex: Validate MCP server connectivity and list available tools
```

---

### Task 0.3: Setup FastAPI Backend Skeleton

**Priority**: P0  
**Estimated Time**: 45 minutes  
**Dependencies**: Task 0.1

**Files to Create:**

- `backend/requirements.txt`
- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/.env.example`

**Steps:**

1. Create `requirements.txt`:

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
httpx==0.26.0
youtube-transcript-api==0.6.2
langchain==0.1.0
langchain-openai==0.0.2
openai==1.10.0
opik-sdk==0.1.0
tower-sdk==0.2.0
PyPDF2==3.0.1
python-multipart==0.0.6
pytest==7.4.0
pytest-asyncio==0.21.0
pytest-cov==4.1.0
black==24.1.0
ruff==0.1.0
```

2. Create minimal `main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title="YouTube Fact-Checker API",
    version="0.1.0",
    description="Verify YouTube claims against company reports"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

3. Create `config.py`:

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    OPIK_API_KEY: str
    OPIK_WORKSPACE: str = "youtube-fact-checker"
    RUNPOD_API_KEY: str = ""
    BACKEND_SECRET_KEY: str
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"

settings = Settings()
```

**Validation:**

- [ ] `uvicorn app.main:app --reload` runs successfully
- [ ] `http://localhost:8000/health` returns 200
- [ ] `http://localhost:8000/docs` shows Swagger UI

**Test Location:** `tests/backend/test_main.py`

---

### Task 0.4: Setup Tower CLI and Authentication

**Priority**: P0  
**Estimated Time**: 20 minutes  
**Dependencies**: None

**Steps:**

1. Install Tower CLI (if not installed)
2. Authenticate: `tower login`
3. List teams: `tower teams list`
4. Switch to workspace: `tower teams switch <team-name>`

**Codex Commands:**

```bash
codex: Use tower_teams_list to show available teams
codex: Use tower_teams_switch to switch to the development team
```

**Validation:**

- [ ] Tower CLI authenticated
- [ ] Can list teams
- [ ] Switched to correct workspace

---

### Task 0.5: Setup Testing Framework

**Priority**: P0  
**Estimated Time**: 30 minutes  
**Dependencies**: Task 0.3

**Files to Create:**

- `pytest.ini`
- `tests/conftest.py`
- `tests/backend/test_main.py`

**Steps:**

1. Create `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
```

2. Create `tests/conftest.py`:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def sample_youtube_url():
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

@pytest.fixture
def sample_company():
    return {
        "company_id": "duolingo",
        "name": "Duolingo",
        "ticker": "DUOL"
    }
```

3. Create first test:

```python
# tests/backend/test_main.py
def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
```

**Validation:**

- [ ] `pytest` runs successfully
- [ ] Coverage report generated
- [ ] All setup tests pass

---

## Phase 1: Document Ingestion (Tower Apps)

### Task 1.1: Create Iceberg Schema for Companies Table

**Priority**: P0  
**Estimated Time**: 30 minutes  
**Dependencies**: Task 0.4

**Files to Create:**

- `tower/schemas/companies.sql`
- `tower/apps/schema-setup/Towerfile`
- `tower/apps/schema-setup/main.py`

**Steps:**

1. Create `companies.sql`:

```sql
CREATE TABLE IF NOT EXISTS companies (
    company_id STRING NOT NULL,
    name STRING NOT NULL,
    ticker STRING,
    industry STRING,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP
) USING iceberg
PARTITIONED BY (bucket(16, company_id))
TBLPROPERTIES (
    'format-version'='2',
    'write.metadata.delete-after-commit.enabled'='true'
);
```

2. Generate Towerfile:

```bash
codex: Generate a Towerfile for schema-setup app with Python 3.11 runtime
```

3. Create handler in `main.py`:

```python
import logging
from tower_sdk import TowerClient

logger = logging.getLogger(__name__)

def handler(event, context):
    """Create Iceberg tables for the fact-checker."""
    try:
        client = TowerClient()

        # Read SQL file
        with open('companies.sql', 'r') as f:
            sql = f.read()

        # Execute
        client.execute_sql(sql)

        logger.info("Companies table created successfully")
        return {"status": "success", "table": "companies"}

    except Exception as e:
        logger.error(f"Failed to create table: {e}")
        return {"status": "error", "error": str(e)}
```

**Validation:**

- [ ] Towerfile validates: `codex: Validate tower/apps/schema-setup/Towerfile`
- [ ] Runs locally: `codex: Run schema-setup locally`
- [ ] Deploys successfully: `codex: Deploy schema-setup app`

**Test Location:** `tests/tower/schema-setup/test_companies_table.py`

---

### Task 1.2: Create Documents Table Schema

**Priority**: P0  
**Estimated Time**: 30 minutes  
**Dependencies**: Task 1.1

**Files to Create:**

- `tower/schemas/documents.sql`

**Schema:**

```sql
CREATE TABLE IF NOT EXISTS documents (
    document_id STRING NOT NULL,
    company_id STRING NOT NULL,
    fiscal_period STRING NOT NULL,  -- Q1, Q2, Q3, Q4, 10-K
    fiscal_year INT NOT NULL,
    pdf_hash STRING NOT NULL,       -- SHA256 of original PDF
    pdf_url STRING,
    pdf_size_bytes BIGINT,
    upload_timestamp TIMESTAMP NOT NULL,
    parser_version STRING NOT NULL,
    status STRING NOT NULL,         -- processing, completed, failed
    metadata MAP<STRING, STRING>,
    created_at TIMESTAMP NOT NULL
) USING iceberg
PARTITIONED BY (company_id, fiscal_year)
TBLPROPERTIES (
    'format-version'='2',
    'write.metadata.delete-after-commit.enabled'='true'
);

-- Index for hash lookups
CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(pdf_hash);
```

**Update schema-setup app** to create this table too.

**Validation:**

- [ ] Table created in Tower
- [ ] Can insert test document
- [ ] Hash index works

**Test Location:** `tests/tower/schema-setup/test_documents_table.py`

---

### Task 1.3: Create Chunks Table Schema

**Priority**: P0  
**Estimated Time**: 45 minutes  
**Dependencies**: Task 1.2

**Files to Create:**

- `tower/schemas/chunks.sql`

**Schema:**

```sql
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id STRING NOT NULL,
    document_id STRING NOT NULL,
    content_normalized STRING NOT NULL,
    content_raw STRING,
    embedding ARRAY<FLOAT>,          -- OpenAI embedding vector
    page_number INT NOT NULL,
    chunk_index INT NOT NULL,        -- Position in document
    section_title STRING,
    bbox STRUCT<                     -- Bounding box coordinates
        x1: FLOAT,
        y1: FLOAT,
        x2: FLOAT,
        y2: FLOAT
    >,
    token_count INT,
    metadata MAP<STRING, STRING>,
    created_at TIMESTAMP NOT NULL
) USING iceberg
PARTITIONED BY (document_id)
TBLPROPERTIES (
    'format-version'='2',
    'write.metadata.delete-after-commit.enabled'='true'
);

-- Foreign key constraint (logical, not enforced in Iceberg)
-- ALTER TABLE chunks ADD CONSTRAINT fk_document
-- FOREIGN KEY (document_id) REFERENCES documents(document_id);
```

**Validation:**

- [ ] Table created successfully
- [ ] Can insert chunks with embeddings
- [ ] Partitioning works correctly

**Test Location:** `tests/tower/schema-setup/test_chunks_table.py`

---

### Task 1.4: Create Document Ingestion Tower App

**Priority**: P1  
**Estimated Time**: 2 hours  
**Dependencies**: Task 1.2

**Files to Create:**

- `tower/apps/document-ingestion/Towerfile`
- `tower/apps/document-ingestion/main.py`
- `tower/apps/document-ingestion/requirements.txt`

**Steps:**

1. Generate Towerfile:

```yaml
name: document-ingestion
description: Ingest PDF documents and generate hashes
runtime: python3.11
handler: main.handler
timeout: 600
memory: 1024
env:
  - name: PARSER_VERSION
    value: "1.0.0"
```

2. Create handler:

```python
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any
import httpx
from tower_sdk import TowerClient

logger = logging.getLogger(__name__)

async def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Ingest a PDF document.

    Event schema:
    {
        "company_id": "duolingo",
        "fiscal_period": "Q1",
        "fiscal_year": 2024,
        "pdf_url": "https://...",
        "pdf_binary": "base64..." (optional, if URL not provided)
    }
    """
    try:
        company_id = event["company_id"]
        fiscal_period = event["fiscal_period"]
        fiscal_year = event["fiscal_year"]

        # Download or use provided binary
        if "pdf_url" in event:
            pdf_binary = await download_pdf(event["pdf_url"])
            pdf_url = event["pdf_url"]
        else:
            import base64
            pdf_binary = base64.b64decode(event["pdf_binary"])
            pdf_url = None

        # Generate hash
        pdf_hash = hashlib.sha256(pdf_binary).hexdigest()

        # Check if already exists
        client = TowerClient()
        existing = client.query(
            f"SELECT document_id FROM documents WHERE pdf_hash = '{pdf_hash}'"
        )

        if existing:
            logger.info(f"Document already exists: {existing[0]['document_id']}")
            return {
                "status": "exists",
                "document_id": existing[0]["document_id"],
                "pdf_hash": pdf_hash
            }

        # Create document ID
        document_id = f"{company_id}_{fiscal_period}_{fiscal_year}_{pdf_hash[:8]}"

        # Insert into documents table
        client.execute_sql(f"""
            INSERT INTO documents VALUES (
                '{document_id}',
                '{company_id}',
                '{fiscal_period}',
                {fiscal_year},
                '{pdf_hash}',
                '{pdf_url}',
                {len(pdf_binary)},
                current_timestamp(),
                '{context.env.get("PARSER_VERSION", "1.0.0")}',
                'processing',
                map(),
                current_timestamp()
            )
        """)

        logger.info(f"Document ingested: {document_id}")

        return {
            "status": "success",
            "document_id": document_id,
            "pdf_hash": pdf_hash,
            "size_bytes": len(pdf_binary)
        }

    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }

async def download_pdf(url: str) -> bytes:
    """Download PDF from URL."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=60.0)
        response.raise_for_status()
        return response.content
```

**Validation:**

- [ ] Towerfile validates
- [ ] Handles duplicate PDFs correctly
- [ ] Generates correct SHA256 hash
- [ ] Stores metadata properly

**Test Location:** `tests/tower/document-ingestion/test_ingestion.py`

**Codex Commands:**

```bash
codex: Validate tower/apps/document-ingestion/Towerfile
codex: Test document-ingestion locally with sample PDF URL
codex: Deploy document-ingestion app
```

---

### Task 1.5: Create Chunk Storage Tower App

**Priority**: P1  
**Estimated Time**: 1.5 hours  
**Dependencies**: Task 1.3, Task 1.4

**Files to Create:**

- `tower/apps/chunk-storage/Towerfile`
- `tower/apps/chunk-storage/main.py`

**Handler Logic:**

```python
from typing import Dict, Any, List
import logging
from tower_sdk import TowerClient
import uuid

logger = logging.getLogger(__name__)

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Store chunks for a document.

    Event schema:
    {
        "document_id": "duolingo_Q1_2024_abc123",
        "chunks": [
            {
                "content_normalized": "Revenue increased...",
                "content_raw": "Revenue increased...",
                "embedding": [0.1, 0.2, ...],
                "page_number": 5,
                "chunk_index": 0,
                "section_title": "Financial Results",
                "bbox": {"x1": 0, "y1": 0, "x2": 100, "y2": 100},
                "token_count": 150
            }
        ]
    }
    """
    try:
        document_id = event["document_id"]
        chunks = event["chunks"]

        client = TowerClient()

        # Verify document exists
        doc_check = client.query(
            f"SELECT document_id FROM documents WHERE document_id = '{document_id}'"
        )
        if not doc_check:
            raise ValueError(f"Document not found: {document_id}")

        # Insert chunks
        chunk_ids = []
        for chunk in chunks:
            chunk_id = str(uuid.uuid4())

            # Prepare embedding array
            embedding_str = "[" + ",".join(str(x) for x in chunk["embedding"]) + "]"

            client.execute_sql(f"""
                INSERT INTO chunks VALUES (
                    '{chunk_id}',
                    '{document_id}',
                    '{chunk["content_normalized"]}',
                    '{chunk.get("content_raw", "")}',
                    {embedding_str},
                    {chunk["page_number"]},
                    {chunk["chunk_index"]},
                    '{chunk.get("section_title", "")}',
                    named_struct(
                        'x1', {chunk["bbox"]["x1"]},
                        'y1', {chunk["bbox"]["y1"]},
                        'x2', {chunk["bbox"]["x2"]},
                        'y2', {chunk["bbox"]["y2"]}
                    ),
                    {chunk.get("token_count", 0)},
                    map(),
                    current_timestamp()
                )
            """)
            chunk_ids.append(chunk_id)

        # Update document status
        client.execute_sql(f"""
            UPDATE documents
            SET status = 'completed'
            WHERE document_id = '{document_id}'
        """)

        logger.info(f"Stored {len(chunk_ids)} chunks for {document_id}")

        return {
            "status": "success",
            "document_id": document_id,
            "chunk_count": len(chunk_ids),
            "chunk_ids": chunk_ids
        }

    except Exception as e:
        logger.error(f"Chunk storage failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }
```

**Validation:**

- [ ] Stores chunks with embeddings
- [ ] Links to document correctly
- [ ] Updates document status
- [ ] Handles errors gracefully

**Test Location:** `tests/tower/chunk-storage/test_chunk_storage.py`

---

## Phase 2: PDF Processing Pipeline (ETL)

### Task 2.1: Implement PDF Downloader

**Priority**: P1  
**Estimated Time**: 1 hour  
**Dependencies**: None

**Files to Create:**

- `etl/pdf_downloader.py`
- `etl/__init__.py`

**Implementation:**

```python
import httpx
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class PDFDownloader:
    """Download PDFs from URLs with retry logic."""

    def __init__(self, timeout: int = 60, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries

    async def download(
        self,
        url: str,
        save_path: Optional[Path] = None
    ) -> bytes:
        """
        Download PDF from URL.

        Args:
            url: PDF URL
            save_path: Optional path to save PDF

        Returns:
            PDF binary content

        Raises:
            httpx.HTTPError: On download failure
        """
        async with httpx.AsyncClient() as client:
            for attempt in range(self.max_retries):
                try:
                    logger.info(f"Downloading PDF (attempt {attempt + 1}): {url}")
                    response = await client.get(url, timeout=self.timeout)
                    response.raise_for_status()

                    content = response.content

                    # Validate it's actually a PDF
                    if not content.startswith(b'%PDF'):
                        raise ValueError("Downloaded file is not a valid PDF")

                    if save_path:
                        save_path.write_bytes(content)
                        logger.info(f"Saved PDF to {save_path}")

                    return content

                except (httpx.HTTPError, ValueError) as e:
                    if attempt == self.max_retries - 1:
                        raise
                    logger.warning(f"Download failed, retrying: {e}")

        raise RuntimeError("Failed to download PDF after retries")

    async def download_sec_filing(
        self,
        ticker: str,
        filing_type: str,
        fiscal_year: int,
        fiscal_period: Optional[str] = None
    ) -> bytes:
        """
        Download SEC filing from EDGAR.

        Args:
            ticker: Company ticker symbol
            filing_type: "10-Q" or "10-K"
            fiscal_year: Year of filing
            fiscal_period: For 10-Q: "Q1", "Q2", "Q3"

        Returns:
            PDF content
        """
        # SEC EDGAR URL construction
        # This is simplified - real implementation needs CIK lookup
        base_url = "https://www.sec.gov/cgi-bin/browse-edgar"

        # Implementation would query EDGAR API here
        # For now, raise not implemented
        raise NotImplementedError("SEC EDGAR integration pending")
```

**Validation:**

- [ ] Downloads valid PDFs
- [ ] Retries on failure
- [ ] Validates PDF format
- [ ] Handles errors gracefully

**Test Location:** `tests/etl/test_pdf_downloader.py`

---

### Task 2.2: Setup RunPod GPU Instance for OCR

**Priority**: P1  
**Estimated Time**: 1.5 hours  
**Dependencies**: None

**Steps:**

1. Create RunPod account
2. Deploy GPU pod with Docker image containing marker-pdf
3. Create REST API endpoint for PDF processing
4. Document endpoint URL and API key

**Files to Create:**

- `etl/runpod_client.py`
- `scripts/runpod_setup.md`

**Client Implementation:**

```python
import httpx
import base64
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class RunPodClient:
    """Client for RunPod GPU inference."""

    def __init__(self, api_key: str, endpoint_id: str):
        self.api_key = api_key
        self.endpoint_url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def process_pdf(self, pdf_binary: bytes) -> Dict[str, Any]:
        """
        Process PDF with marker-pdf on RunPod.

        Args:
            pdf_binary: PDF file content

        Returns:
            Parsed PDF structure with text, pages, bbox coordinates
        """
        # Encode PDF as base64
        pdf_b64 = base64.b64encode(pdf_binary).decode()

        payload = {
            "input": {
                "pdf_data": pdf_b64,
                "include_bbox": True,
                "include_page_numbers": True
            }
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            # Submit job
            response = await client.post(
                self.endpoint_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            job_data = response.json()

            job_id = job_data["id"]
            logger.info(f"RunPod job submitted: {job_id}")

            # Poll for results
            status_url = f"https://api.runpod.ai/v2/{job_id}/status"

            while True:
                status_resp = await client.get(status_url, headers=self.headers)
                status_data = status_resp.json()

                if status_data["status"] == "COMPLETED":
                    return status_data["output"]
                elif status_data["status"] == "FAILED":
                    raise RuntimeError(f"RunPod job failed: {status_data.get('error')}")

                await asyncio.sleep(5)  # Poll every 5 seconds
```

**Validation:**

- [ ] RunPod endpoint accessible
- [ ] Can process sample PDF
- [ ] Returns structured data with bbox
- [ ] Handles large PDFs (50+ pages)

**Test Location:** `tests/etl/test_runpod_client.py`

---

Continue with remaining tasks in next message due to length...

Would you like me to continue with the remaining phases (2.3-8.0)?
