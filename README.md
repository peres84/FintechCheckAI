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

## Quick Start

### Option 1: Local Development (Recommended for Development)

#### Backend

1. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start the server:**
   ```bash
   python main.py
   ```
   
   For development with auto-reload:
   ```bash
   python main.py --reload
   ```

   The API will be available at `http://127.0.0.1:8000`
   - API Docs: http://127.0.0.1:8000/docs
   - Health Check: http://127.0.0.1:8000/health

#### Frontend

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Set up environment variables (optional):**
   ```bash
   cp .env.example .env
   # Edit .env if backend is on different URL
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:8080`

### Option 2: Docker (Recommended for Production/Testing)

#### Full Stack (Backend + Frontend)

```bash
# Start both services
docker-compose up

# Or in detached mode
docker-compose up -d
```

#### Backend Only

```bash
# Start backend service
docker-compose up backend
```

#### Frontend Only

```bash
# Start frontend service
docker-compose up frontend
```

See [DOCKER_SETUP.md](DOCKER_SETUP.md) for detailed Docker instructions.

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions to:
- **Backend:** Render, Railway, Heroku, DigitalOcean
- **Frontend:** Vercel, Netlify, Railway

## Environment Variables

See `.env.example` for required keys. Required variables:
- `OPENAI_API_KEY` - OpenAI API key for AI services
- `RUNPOD_API_KEY` - RunPod API key for audio transcription
- `RUNPOD_ENDPOINT_ID` - RunPod endpoint ID
- `IMAGEKIT_PRIVATE_KEY` - ImageKit private key
- `IMAGEKIT_URL_ENDPOINT` - ImageKit URL endpoint
- `TOWER_API_KEY` - Tower.dev API key (optional)
- `OPIK_API_KEY` - Opik API key (optional)
