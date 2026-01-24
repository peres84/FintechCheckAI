# Fintech Check AI

A fact-checking platform that verifies claims made in YouTube videos against official company quarterly reports with immutable versioned storage.

## Stack

- FastAPI (Python 3.11+)
- Tower.dev + Apache Iceberg
- RunPod (OCR via Marker-PDF/DocTR)
- LangChain + OpenAI
- Opik for observability

## Repository layout

- backend/ - FastAPI application and services
- tower/ - Tower apps and Iceberg schemas
- agents/ - claim extraction and verification agents
- etl/ - PDF processing pipeline utilities
- frontend/ - static landing page (Phase 6)
- docs/ - architecture and API docs

## Quick start

1) Create a virtual environment and install dependencies:

```bash
cd backend
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2) Start the API server:

```bash
uvicorn app.main:app --reload
```

3) Open the landing page:

```bash
start ../frontend/index.html
```

## Environment variables

See `.env.example` for required keys.
