# Development Tasks - Fintech Check AI

## Phase 0: Setup & Infrastructure

### Task 0.1: Initialize Project Structure

**Priority**: P0  
**Estimated Time**: 20 minutes  
**Dependencies**: None

**Steps:**

```bash
mkdir -p fintech-check-ai/{backend/{api/routes,core,services,agents,etl,tower/{apps,schemas},models},tests/{api,services,agents,etl,tower,fixtures},frontend,scripts,docs,.codex}
cd fintech-check-ai
```

**Validation:**

- [ ] Directory structure matches PRD
- [ ] All folders created
- [ ] No nested `app/` folder in backend

---

### Task 0.2: Initialize UV Project

**Priority**: P0  
**Estimated Time**: 30 minutes  
**Dependencies**: Task 0.1

**Files to Create:**

- `pyproject.toml` (in root)
- `.gitignore`

**Steps:**

1. Initialize UV project:

```bash
cd fintech-check-ai
uv init
```

2. Create `pyproject.toml`:

```toml
[project]
name = "fintech-check-ai"
version = "0.1.0"
description = "YouTube fact-checker for financial claims"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.26.0",
    "youtube-transcript-api>=0.6.2",
    "langchain>=0.1.0",
    "langchain-openai>=0.0.2",
    "openai>=1.10.0",
    "opik-sdk>=0.1.0",
    "tower-sdk>=0.2.0",
    "PyPDF2>=3.0.1",
    "python-multipart>=0.0.6",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "black>=24.1.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

3. Create `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
.venv/
venv/
ENV/
env/

# UV
.uv/
uv.lock

# Environment variables
.env
.env.local

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# Tower
.tower/

# Logs
*.log
```

4. Install dependencies:

```bash
uv sync
uv sync --dev
```

**Validation:**

- [ ] `pyproject.toml` created with all dependencies
- [ ] `uv sync` runs successfully
- [ ] Virtual environment created
- [ ] Can run `uv run python --version`

**Test Command:**

```bash
uv run python -c "import fastapi; import langchain; import opik; print('All imports successful')"
```

---

### Task 0.3: Configure Codex CLI with MCP Servers

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

### Task 0.4: Setup FastAPI Backend

**Priority**: P0  
**Estimated Time**: 45 minutes  
**Dependencies**: Task 0.2

**Files to Create:**

- `backend/main.py`
- `backend/core/config.py`
- `backend/core/logging.py`
- `.env.example`

**Steps:**

1. Create `backend/core/config.py`:

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Fintech Check AI"

    # OpenAI
    OPENAI_API_KEY: str

    # Opik
    OPIK_API_KEY: str
    OPIK_WORKSPACE: str = "fintech-check-ai"

    # RunPod
    RUNPOD_API_KEY: str = ""
    RUNPOD_ENDPOINT_ID: str = ""

    # Security
    BACKEND_SECRET_KEY: str
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Tower (optional)
    TOWER_API_KEY: str = ""
    TOWER_WORKSPACE: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

2. Create `backend/core/logging.py`:

```python
import logging
import sys
from pathlib import Path

def setup_logging(log_level: str = "INFO"):
    """Configure logging for the application."""

    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure handlers
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / "app.log")
    ]

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
```

3. Create `backend/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.core.logging import setup_logging

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="Verify YouTube claims against company reports",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": "0.1.0"
    }

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Fintech Check AI",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
```

4. Create `.env.example`:

```bash
# OpenAI
OPENAI_API_KEY=sk-your-key-here

# Opik
OPIK_API_KEY=your-opik-key
OPIK_WORKSPACE=fintech-check-ai

# RunPod (optional)
RUNPOD_API_KEY=
RUNPOD_ENDPOINT_ID=

# Tower (optional)
TOWER_API_KEY=
TOWER_WORKSPACE=

# FastAPI
BACKEND_SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

**Validation:**

- [ ] `uv run uvicorn backend.main:app --reload` runs successfully
- [ ] `http://localhost:8000/health` returns 200
- [ ] `http://localhost:8000/docs` shows Swagger UI
- [ ] CORS headers present in response

**Test Location:** `tests/api/test_main.py`

---

### Task 0.5: Setup Testing Framework

**Priority**: P0  
**Estimated Time**: 30 minutes  
**Dependencies**: Task 0.4

**Files to Create:**

- `tests/conftest.py`
- `tests/api/test_main.py`

**Steps:**

1. Create `tests/conftest.py`:

```python
import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)

@pytest.fixture
def sample_youtube_url():
    """Sample YouTube URL for testing."""
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

@pytest.fixture
def sample_company():
    """Sample company data."""
    return {
        "company_id": "duolingo",
        "name": "Duolingo",
        "ticker": "DUOL"
    }

@pytest.fixture
def sample_pdf_url():
    """Sample PDF URL."""
    return "https://s201.q4cdn.com/217658912/files/doc_financials/2024/q3/DUOL-Q3-2024-Earnings-Presentation.pdf"

@pytest.fixture
def sample_transcript():
    """Sample YouTube transcript."""
    return {
        "video_id": "dQw4w9WgXcQ",
        "segments": [
            {"text": "Duolingo reported revenue of $150 million", "start": 0.0, "duration": 3.5},
            {"text": "This represents a 40% year-over-year growth", "start": 3.5, "duration": 3.0}
        ]
    }
```

2. Create `tests/api/test_main.py`:

```python
import pytest

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "project" in data

def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data

def test_docs_available(client):
    """Test that OpenAPI docs are available."""
    response = client.get("/docs")
    assert response.status_code == 200

def test_cors_headers(client):
    """Test CORS headers are present."""
    response = client.options("/health")
    assert response.status_code == 200
```

**Validation:**

- [ ] `uv run pytest` runs successfully
- [ ] All tests pass
- [ ] Coverage report generated with `uv run pytest --cov=backend`

---

### Task 0.6: Setup Tower CLI and Authentication

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

### Task 0.7: Initialize Opik Service

**Priority**: P0  
**Estimated Time**: 45 minutes  
**Dependencies**: Task 0.4

**Files to Create:**

- `backend/services/opik_service.py`
- `tests/services/test_opik_service.py`

**Steps:**

1. Create `backend/services/opik_service.py`:

```python
import logging
from typing import Optional, Dict, Any
from opik import Opik
from opik.decorators import track
from backend.core.config import settings

logger = logging.getLogger(__name__)

class OpikService:
    """Service for Opik telemetry and tracking."""

    def __init__(self):
        """Initialize Opik client."""
        try:
            self.client = Opik(
                workspace=settings.OPIK_WORKSPACE,
                api_key=settings.OPIK_API_KEY
            )
            logger.info(f"Opik initialized with workspace: {settings.OPIK_WORKSPACE}")
        except Exception as e:
            logger.error(f"Failed to initialize Opik: {e}")
            raise

    @track(name="claim_extraction")
    def track_claim_extraction(
        self,
        transcript: str,
        claims: list,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track claim extraction from transcript.

        Args:
            transcript: Input transcript text
            claims: Extracted claims
            metadata: Additional metadata

        Returns:
            Tracking data
        """
        tracking_data = {
            "input": {
                "transcript_length": len(transcript),
                "transcript_preview": transcript[:200]
            },
            "output": {
                "claims_count": len(claims),
                "claims": claims
            }
        }

        if metadata:
            tracking_data["metadata"] = metadata

        logger.info(f"Tracked claim extraction: {len(claims)} claims")
        return tracking_data

    @track(name="chunk_retrieval")
    def track_chunk_retrieval(
        self,
        query: str,
        chunks: list,
        scores: list,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track chunk retrieval for RAG.

        Args:
            query: Search query
            chunks: Retrieved chunks
            scores: Relevance scores
            metadata: Additional metadata

        Returns:
            Tracking data
        """
        tracking_data = {
            "input": {"query": query},
            "output": {
                "chunks_count": len(chunks),
                "avg_score": sum(scores) / len(scores) if scores else 0,
                "chunks": chunks
            }
        }

        if metadata:
            tracking_data["metadata"] = metadata

        logger.info(f"Tracked chunk retrieval: {len(chunks)} chunks")
        return tracking_data

    @track(name="verification")
    def track_verification(
        self,
        claim: str,
        chunks: list,
        verdict: str,
        reasoning: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track claim verification.

        Args:
            claim: Claim to verify
            chunks: Retrieved context chunks
            verdict: Verification verdict
            reasoning: Verification reasoning
            metadata: Additional metadata

        Returns:
            Tracking data
        """
        tracking_data = {
            "input": {"claim": claim},
            "context": {"chunks": chunks},
            "output": {
                "verdict": verdict,
                "reasoning": reasoning
            }
        }

        if metadata:
            tracking_data["metadata"] = metadata

        logger.info(f"Tracked verification: {verdict}")
        return tracking_data

    def log_error(
        self,
        operation: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log error to Opik.

        Args:
            operation: Operation that failed
            error: Exception that occurred
            context: Additional context
        """
        error_data = {
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }

        logger.error(f"Opik error log: {error_data}")
        # Opik will automatically capture this through decorators

# Global instance
opik_service = OpikService()
```

2. Create `tests/services/test_opik_service.py`:

```python
import pytest
from backend.services.opik_service import OpikService

def test_opik_service_initialization():
    """Test Opik service can be initialized."""
    service = OpikService()
    assert service.client is not None

def test_track_claim_extraction():
    """Test claim extraction tracking."""
    service = OpikService()
    transcript = "Duolingo reported $150M revenue"
    claims = ["Revenue: $150M"]

    result = service.track_claim_extraction(transcript, claims)

    assert result["input"]["transcript_length"] == len(transcript)
    assert result["output"]["claims_count"] == 1

def test_track_chunk_retrieval():
    """Test chunk retrieval tracking."""
    service = OpikService()
    query = "revenue Q3 2024"
    chunks = ["chunk1", "chunk2"]
    scores = [0.9, 0.8]

    result = service.track_chunk_retrieval(query, chunks, scores)

    assert result["output"]["chunks_count"] == 2
    assert result["output"]["avg_score"] == 0.85

def test_track_verification():
    """Test verification tracking."""
    service = OpikService()
    claim = "Revenue was $150M"
    chunks = ["context chunk"]
    verdict = "VERIFIED"
    reasoning = "Found in Q3 report"

    result = service.track_verification(claim, chunks, verdict, reasoning)

    assert result["output"]["verdict"] == "VERIFIED"
    assert result["output"]["reasoning"] == reasoning
```

**Validation:**

- [ ] Opik service initializes successfully
- [ ] Can track operations
- [ ] Tests pass
- [ ] Opik dashboard shows tracked operations

**Test Command:**

```bash
uv run pytest tests/services/test_opik_service.py -v
```

---

## Phase 1: Document Ingestion (Tower Apps)

### Task 1.1: Create Iceberg Schema for Companies Table

**Priority**: P0  
**Estimated Time**: 30 minutes  
**Dependencies**: Task 0.6

**Files to Create:**

- `backend/tower/schemas/companies.sql`
- `backend/tower/apps/schema-setup/Towerfile`
- `backend/tower/apps/schema-setup/main.py`

**Steps:**

1. Create `backend/tower/schemas/companies.sql`:

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

Or manually create `backend/tower/apps/schema-setup/Towerfile`:

```yaml
name: schema-setup
description: Create Iceberg tables for Fintech Check AI
runtime: python3.11
handler: main.handler
timeout: 300
memory: 512
```

3. Create `backend/tower/apps/schema-setup/main.py`:

```python
import logging
from pathlib import Path
from tower_sdk import TowerClient

logger = logging.getLogger(__name__)

def handler(event, context):
    """Create Iceberg tables for the fact-checker."""
    try:
        client = TowerClient()

        # Read and execute companies.sql
        companies_sql = Path(__file__).parent.parent.parent / "schemas" / "companies.sql"
        with open(companies_sql, 'r') as f:
            sql = f.read()

        client.execute_sql(sql)
        logger.info("Companies table created successfully")

        return {
            "status": "success",
            "table": "companies",
            "message": "Table created or already exists"
        }

    except Exception as e:
        logger.error(f"Failed to create companies table: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
```

**Validation:**

- [ ] Towerfile validates: `codex: Validate backend/tower/apps/schema-setup/Towerfile`
- [ ] Runs locally: `codex: Run schema-setup locally`
- [ ] Deploys successfully: `codex: Deploy schema-setup app`

**Test Location:** `tests/tower/test_schema_setup.py`

---

Continue with remaining tasks...

Would you like me to continue with the rest of the tasks (1.2-2.2 and beyond)?
