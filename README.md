# Fintech Check AI

A fact-checking platform that verifies claims made in YouTube videos against official company quarterly reports with immutable versioned storage.

## Stack

- FastAPI (Python 3.11+)
- UV (Python package manager)
- Tower.dev + Apache Iceberg
- RunPod (OCR via Marker-PDF/DocTR)
- LangChain + OpenAI
- Opik for observability

## Repository layout

- backend/ - FastAPI app, services, agents, ETL, and Tower apps
- tests/ - API, services, agents, ETL, and Tower tests
- frontend/ - static landing page assets
- docs/ - architecture and API docs

## Quick start

1) Create a virtual environment and install dependencies:

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install uv
uv pip install -e ./backend
```

2) Start the API server:

```bash
uvicorn backend.main:app --reload
```

3) Open the landing page:

```bash
start ../frontend/index.html
```

## Environment variables

See `.env.example` for required keys.
