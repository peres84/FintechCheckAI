# Codex CLI Initialization - Fintech Check AI

## Project Context

This is a YouTube fact-checking platform that verifies claims against official company quarterly reports using Tower.dev, FastAPI, and LangChain. Package management is done with UV.

## MCP Servers Configuration

### Context7

- **Purpose**: Documentation queries for libraries and frameworks
- **Status**: Enabled
- **Auth**: Unsupported
- **Command**: `npx -y @upstash/context7-mcp --api-key ctx7sk-c786f128-6b01-4557-be68-e5b6a723e7ba`
- **Available Tools**:
  - `query-docs`: Query documentation for any library
  - `resolve-library-id`: Get library IDs for documentation
- **Usage**: Use for FastAPI, LangChain, Tower SDK, UV questions

### Magic

- **Purpose**: UI component generation and inspiration
- **Status**: Enabled
- **Auth**: Requires API_KEY environment variable
- **Command**: `npx -y @21st-dev/magic@latest`
- **Environment**: `API_KEY=*****`
- **Available Tools**:
  - `21st_magic_component_builder`: Build UI components
  - `21st_magic_component_inspiration`: Get design ideas
  - `21st_magic_component_refiner`: Refine existing components
  - `logo_search`: Search for logos
- **Usage**: Generate landing page components, results display UI

### Tower

- **Purpose**: Tower.dev data platform operations
- **Status**: Enabled
- **Auth**: Unsupported (uses Tower CLI authentication)
- **Command**: `tower mcp-server`
- **Available Tools**:
  - **Apps**: `tower_apps_create`, `tower_apps_delete`, `tower_apps_list`, `tower_apps_logs`, `tower_apps_show`
  - **Deployment**: `tower_deploy`
  - **Files**: `tower_file_add_parameter`, `tower_file_generate`, `tower_file_read`, `tower_file_update`, `tower_file_validate`
  - **Execution**: `tower_run_local`, `tower_run_remote`
  - **Schedules**: `tower_schedules_create`, `tower_schedules_delete`, `tower_schedules_list`, `tower_schedules_update`
  - **Secrets**: `tower_secrets_create`, `tower_secrets_delete`, `tower_secrets_list`
  - **Teams**: `tower_teams_list`, `tower_teams_switch`
  - **Help**: `tower_workflow_help`
- **Usage**: Create Tower apps, manage Iceberg tables, deploy workflows

## Development Workflow

### 1. Starting New Features

```bash
# Always validate Tower files before deploying
codex: Use tower_file_validate to check Towerfile syntax

# Create new Tower app
codex: Use tower_apps_create to create a new app called "document-ingestion"

# Query documentation when needed
codex: Use query-docs from Context7 to learn about FastAPI dependency injection

# Query UV documentation
codex: Use query-docs from Context7 to learn about UV package management
```

### 2. Testing Strategy

Each feature should be developed in isolation with its own test file:

**All tests are in the root `tests/` folder:**

```
tests/
├── api/
│   ├── test_youtube_api.py
│   └── test_verification_api.py
├── services/
│   ├── test_youtube_service.py
│   ├── test_opik_service.py
│   └── test_rag_service.py
├── agents/
│   ├── test_claim_extractor.py
│   └── test_verification_agent.py
├── etl/
│   ├── test_pdf_processor.py
│   └── test_normalizer.py
├── tower/
│   ├── test_document_ingestion.py
│   └── test_chunk_storage.py
└── fixtures/
    ├── sample.pdf
    └── sample_transcript.json
```

### 3. UV Package Management

**Why UV?**

- 10-100x faster than pip
- Built-in virtual environment management
- Better dependency resolution
- Lock file support (like npm/yarn)

**Common UV Commands:**

```bash
# Initialize project (creates pyproject.toml)
uv init

# Add dependencies
uv add fastapi uvicorn[standard] pydantic

# Add dev dependencies
uv add --dev pytest pytest-asyncio black ruff

# Install all dependencies
uv sync

# Run commands in UV environment
uv run python backend/main.py
uv run pytest
uv run uvicorn backend.main:app --reload

# Update dependencies
uv lock --upgrade

# Remove dependency
uv remove <package-name>
```

### 4. Tower App Development Workflow

**Required Towerfile Structure** (from Tower docs):

```yaml
# Towerfile (located in backend/tower/apps/<app-name>/)
name: app-name
description: App description
runtime: python3.11
handler: main.handler

# Optional
schedule: "0 0 * * *" # Cron format
timeout: 300 # seconds
memory: 512 # MB
env:
  - name: ENV_VAR
    value: value
secrets:
  - SECRET_NAME
```

**Development Steps:**

1. Create app directory: `backend/tower/apps/<app-name>/`
2. Generate Towerfile: `codex: Use tower_file_generate`
3. Write handler in `main.py`
4. Validate: `codex: Use tower_file_validate`
5. Test locally: `codex: Use tower_run_local`
6. Create tests in `tests/tower/test_<app-name>.py`
7. Deploy: `codex: Use tower_deploy`
8. Check logs: `codex: Use tower_apps_logs --app-name <app-name>`

### 5. Iceberg Table Management

**Creating Tables via Tower Apps:**

```python
# backend/tower/apps/schema-setup/main.py
def handler(event, context):
    from tower_sdk import TowerClient

    client = TowerClient()

    # Create companies table
    client.execute_sql("""
        CREATE TABLE IF NOT EXISTS companies (
            company_id STRING,
            name STRING,
            ticker STRING,
            created_at TIMESTAMP
        ) USING iceberg
        PARTITIONED BY (days(created_at))
    """)

    return {"status": "success"}
```

**Testing Tables:**

```python
# tests/tower/test_schema_setup.py
import pytest
from tower_sdk import TowerClient

def test_companies_table_exists():
    client = TowerClient()
    tables = client.list_tables()
    assert "companies" in tables

def test_insert_company():
    client = TowerClient()
    client.execute_sql("""
        INSERT INTO companies VALUES (
            'duolingo', 'Duolingo', 'DUOL', current_timestamp()
        )
    """)
    result = client.query("SELECT * FROM companies WHERE company_id = 'duolingo'")
    assert len(result) == 1
```

### 6. Opik Service Integration

**Setting up Opik tracking:**

```python
# backend/services/opik_service.py
from opik import Opik
from opik.decorators import track

class OpikService:
    def __init__(self):
        self.client = Opik(
            workspace="fintech-check-ai",
            api_key=settings.OPIK_API_KEY
        )

    @track(name="claim_extraction")
    def track_claim_extraction(self, transcript: str, claims: list):
        """Track claim extraction from transcript."""
        return {
            "input": {"transcript_length": len(transcript)},
            "output": {"claims_count": len(claims), "claims": claims}
        }

    @track(name="verification")
    def track_verification(self, claim: str, chunks: list, verdict: str):
        """Track claim verification."""
        return {
            "input": {"claim": claim},
            "context": {"chunks": chunks},
            "output": {"verdict": verdict}
        }
```

**Using Opik in agents:**

```python
# backend/agents/claim_extractor.py
from backend.services.opik_service import OpikService

class ClaimExtractor:
    def __init__(self):
        self.opik = OpikService()

    def extract_claims(self, transcript: str) -> list:
        # Extract claims with LLM
        claims = self._llm_extract(transcript)

        # Track with Opik
        self.opik.track_claim_extraction(transcript, claims)

        return claims
```

## Code Quality Standards

### Python Standards

- **Package Manager**: UV (fast Python package installer)
- **Formatter**: Black (line length: 100)
- **Linter**: Ruff
- **Type Hints**: Required for all functions
- **Docstrings**: Google style for all public functions
- **Testing**: pytest with ≥80% coverage

### FastAPI Standards

- Use async/await for all endpoints
- Pydantic models for request/response validation
- Dependency injection for services
- Proper HTTP status codes
- OpenAPI documentation for all endpoints

### Tower App Standards

- One responsibility per app
- Idempotent operations
- Proper error handling with try/except
- Return structured JSON responses
- Include logging for debugging

## Environment Variables

Create `.env` file with:

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Opik
OPIK_API_KEY=...
OPIK_WORKSPACE=fintech-check-ai

# RunPod
RUNPOD_API_KEY=...
RUNPOD_ENDPOINT_ID=...

# Tower (if needed for SDK)
TOWER_API_KEY=...
TOWER_WORKSPACE=...

# Magic
MAGIC_API_KEY=...

# FastAPI
BACKEND_SECRET_KEY=...
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

## Common Codex Commands

### UV Package Management

```bash
# Add new dependency
codex: Add langchain and langchain-openai packages using UV

# Update all dependencies
codex: Update all UV dependencies to latest versions

# Show installed packages
codex: List all installed packages with UV
```

### Tower Operations

```bash
# Validate Towerfile before deploying
codex: Validate the Towerfile in backend/tower/apps/document-ingestion/

# Deploy a Tower app
codex: Deploy the document-ingestion app to Tower

# Check app logs
codex: Show logs for the document-ingestion app

# List all deployed apps
codex: List all Tower apps

# Test app locally
codex: Run the chunk-storage app locally with test data
```

### Documentation Queries

```bash
# FastAPI questions
codex: Query Context7 docs for FastAPI file upload best practices

# LangChain questions
codex: Query Context7 docs for LangChain RAG implementation

# UV questions
codex: Query Context7 docs for UV dependency management

# Opik questions
codex: Query Context7 docs for Opik tracking decorators
```

### UI Development

```bash
# Generate landing page
codex: Use Magic to create a landing page component for YouTube URL input

# Create results display
codex: Use Magic to design a results table showing verified claims with citations
```

## Testing Commands

```bash
# Run all tests (from root directory)
uv run pytest

# Run specific test file
uv run pytest tests/tower/test_document_ingestion.py

# Run with coverage
uv run pytest --cov=backend --cov-report=html

# Run only Tower tests
uv run pytest tests/tower/

# Run only API tests
uv run pytest tests/api/

# Run with verbose output
uv run pytest -v

# Run and stop on first failure
uv run pytest -x
```

## File Generation Templates

### FastAPI Endpoint Template

```python
from fastapi import APIRouter, Depends, HTTPException
from backend.models.schemas import RequestModel, ResponseModel
from backend.services.service import Service

router = APIRouter(prefix="/api/endpoint", tags=["endpoint"])

@router.post("/", response_model=ResponseModel)
async def endpoint_handler(
    request: RequestModel,
    service: Service = Depends(get_service)
) -> ResponseModel:
    """
    Endpoint description.

    Args:
        request: Request payload
        service: Injected service

    Returns:
        Response payload

    Raises:
        HTTPException: On validation or processing errors
    """
    try:
        result = await service.process(request)
        return ResponseModel(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Tower App Handler Template

```python
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Tower app handler.

    Args:
        event: Input event data
        context: Tower execution context

    Returns:
        Result dictionary with status and data
    """
    try:
        logger.info(f"Processing event: {event}")

        # Your logic here
        result = process_data(event)

        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }

def process_data(event: Dict[str, Any]) -> Dict[str, Any]:
    """Process the input data."""
    # Implementation
    pass
```

### Test Template

```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def sample_data():
    """Fixture for test data."""
    return {
        "key": "value"
    }

def test_feature(sample_data):
    """Test feature functionality."""
    # Arrange
    expected = "expected_result"

    # Act
    result = function_under_test(sample_data)

    # Assert
    assert result == expected

@pytest.mark.asyncio
async def test_async_feature():
    """Test async functionality."""
    result = await async_function()
    assert result is not None
```

### Opik Tracking Template

```python
from opik.decorators import track
from backend.services.opik_service import OpikService

class MyAgent:
    def __init__(self):
        self.opik = OpikService()

    @track(name="my_operation")
    def my_operation(self, input_data: dict) -> dict:
        """
        Operation with Opik tracking.

        This decorator automatically logs:
        - Input parameters
        - Output results
        - Execution time
        - Any errors
        """
        # Your logic here
        result = process(input_data)
        return result
```

## Development Checklist

Before committing any feature:

- [ ] Code follows style guide (Black formatted, Ruff linted)
- [ ] Type hints added
- [ ] Docstrings added
- [ ] Tests written and passing
- [ ] Tower files validated (if applicable)
- [ ] Environment variables documented
- [ ] Error handling implemented
- [ ] Logging added for debugging
- [ ] Opik tracking added for agents/LLM calls
- [ ] API docs updated (if endpoint added)
- [ ] UV dependencies updated in pyproject.toml

## Debugging Tips

### Tower Apps

```bash
# Check app logs
codex: Show recent logs for document-ingestion app

# Test locally with sample data
codex: Run document-ingestion locally with this event: {"pdf_url": "https://example.com/doc.pdf"}

# Validate Towerfile
codex: Validate Towerfile and show any errors
```

### FastAPI

```bash
# Run with debug logging
uv run uvicorn backend.main:app --reload --log-level debug

# Test endpoint with curl
curl -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{"youtube_url": "...", "company_id": "duolingo"}'
```

### Opik Debugging

```bash
# View traces in Opik dashboard
# Go to https://app.opik.ai and filter by:
# - Workspace: fintech-check-ai
# - Operation name (e.g., "claim_extraction")
# - Time range

# Check for errors in traces
# Failed operations are highlighted in red
# Click on trace to see full context including LLM prompts/responses
```

### Database

```bash
# Query tables via Tower
codex: Query the chunks table and show the first 10 rows

# Check table schema
codex: Show the schema for the documents table
```

## Notes for Codex

- Always use UV for package management (not pip)
- All backend code goes in `backend/` folder (no nested `app/` folder)
- All tests go in root `tests/` folder
- Always validate Tower files before deployment
- Use Context7 for documentation queries before implementing
- Test each component in isolation before integration
- Keep Tower apps small and focused on single responsibility
- Use proper error handling in all async operations
- Log important events for debugging
- Track all agent operations with Opik
- Run tests after any code changes
