# Codex CLI Initialization - Fintech Check AI

## Project Context

This is a YouTube fact-checking platform that verifies claims against official company quarterly reports using Tower.dev, FastAPI, and LangChain.

## MCP Servers Configuration

### Context7

- **Purpose**: Documentation queries for libraries and frameworks
- **Status**: Enabled
- **Auth**: Unsupported
- **Command**: `npx -y @upstash/context7-mcp --api-key ctx7sk-c786f128-6b01-4557-be68-e5b6a723e7ba`
- **Available Tools**:
  - `query-docs`: Query documentation for any library
  - `resolve-library-id`: Get library IDs for documentation
- **Usage**: Use for FastAPI, LangChain, Tower SDK questions

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
```

### 2. Testing Strategy

Each feature should be developed in isolation with its own test file:

**Tower Apps Testing Pattern:**

```
tests/tower/<app-name>/
  ├── test_<app-name>.py
  ├── fixtures/
  │   └── sample_data.json
  └── README.md
```

**Backend Testing Pattern:**

```
tests/backend/<module>/
  ├── test_<feature>.py
  └── conftest.py (shared fixtures)
```

**ETL Testing Pattern:**

```
tests/etl/
  ├── test_pdf_processor.py
  ├── test_normalizer.py
  └── fixtures/
      └── sample.pdf
```

### 3. Tower App Development Workflow

**Required Towerfile Structure** (from Tower docs):

```yaml
# Towerfile
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

1. Create app directory: `tower/apps/<app-name>/`
2. Generate Towerfile: `codex: Use tower_file_generate`
3. Write handler in `main.py`
4. Validate: `codex: Use tower_file_validate`
5. Test locally: `codex: Use tower_run_local`
6. Create tests in `tests/tower/<app-name>/`
7. Deploy: `codex: Use tower_deploy`
8. Check logs: `codex: Use tower_apps_logs --app-name <app-name>`

### 4. Iceberg Table Management

**Creating Tables via Tower Apps:**

```python
# tower/apps/schema-setup/main.py
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

## Code Quality Standards

### Python Standards

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
OPIK_WORKSPACE=youtube-fact-checker

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

### Tower Operations

```bash
# Validate Towerfile before deploying
codex: Validate the Towerfile in tower/apps/document-ingestion/

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

# Tower SDK questions
codex: Query Context7 docs for Tower Python SDK table operations
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
# Run all tests
pytest

# Run specific test file
pytest tests/tower/test_document_ingestion.py

# Run with coverage
pytest --cov=backend --cov-report=html

# Run only Tower tests
pytest tests/tower/

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x
```

## File Generation Templates

### FastAPI Endpoint Template

```python
from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import RequestModel, ResponseModel
from app.services.service import Service

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

## Development Checklist

Before committing any feature:

- [ ] Code follows style guide (Black formatted)
- [ ] Type hints added
- [ ] Docstrings added
- [ ] Tests written and passing
- [ ] Tower files validated (if applicable)
- [ ] Environment variables documented
- [ ] Error handling implemented
- [ ] Logging added for debugging
- [ ] API docs updated (if endpoint added)
- [ ] README updated if needed

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
uvicorn app.main:app --reload --log-level debug

# Test endpoint with curl
curl -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{"youtube_url": "...", "company_id": "duolingo"}'
```

### Database

```bash
# Query tables via Tower
codex: Query the chunks table and show the first 10 rows

# Check table schema
codex: Show the schema for the documents table
```

## Notes for Codex

- Always validate Tower files before deployment
- Use Context7 for documentation queries before implementing
- Test each component in isolation before integration
- Keep Tower apps small and focused on single responsibility
- Use proper error handling in all async operations
- Log important events for debugging
- Run tests after any code changes
