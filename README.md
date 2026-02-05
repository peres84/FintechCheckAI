# Fintech Check AI

A fact-checking platform that verifies claims made in YouTube videos against official company quarterly reports with immutable versioned storage.

## Stack

- FastAPI (Python 3.11+)
- **Node.js 18+** (Required for yt-dlp to extract YouTube videos properly)
- UV (Python package manager)
- Tower.dev + Apache Iceberg
- RunPod (OCR via Marker-PDF/DocTR)
- LangChain + OpenAI
- Opik for observability

## Prerequisites

**⚠️ IMPORTANT: Node.js 18+ is REQUIRED**

Node.js is required for the backend to properly extract audio from YouTube videos when captions are not available. Without Node.js, you will see warnings and some videos may fail to process.

**Install Node.js:**
- **Windows/Mac:** Download from https://nodejs.org/ (LTS version recommended)
- **Linux:** `sudo apt install nodejs npm` (Ubuntu/Debian) or use your package manager
- **Verify installation:** `node --version` (should show v18 or higher)

## Repository layout

- backend/ - FastAPI app, services, agents, ETL, and Tower apps
- tests/ - API, services, agents, ETL, and Tower tests
- frontend/ - static landing page assets
- docs/ - architecture and API docs

## Quick Start

### Option 1: Local Development (Recommended for Development)

**⚠️ Before starting, ensure Node.js 18+ is installed!** Without it, YouTube video processing will fail.

#### Backend

1. **Verify Node.js is installed:**
   ```bash
   node --version  # Should show v18.0.0 or higher
   ```
   
   If Node.js is not installed, download it from https://nodejs.org/

2. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Start the server (IMPORTANT: Run from project root, not backend/):**
   ```bash
   # Make sure you're in the project root directory
   cd C:\Users\Acer\Documents\GitHub\Fintech_CheckAI
   
   # Then run:
   python main.py
   ```
   
   ⚠️ **Don't run from `backend/` directory!** The `main.py` file is in the project root.
   
   For development with auto-reload:
   ```bash
   python main.py --reload
   ```

   The API will be available at `http://127.0.0.1:8000`
   - API Docs: http://127.0.0.1:8000/docs
   - Health Check: http://127.0.0.1:8000/health
   
   **Note:** The warnings about `fitz` (PDF processor) and `opik` are normal - these are optional dependencies.

#### Frontend

1. **Install dependencies (REQUIRED - must run this first!):**
   ```bash
   cd frontend
   npm install
   ```
   
   ⚠️ **Important:** You must run `npm install` before `npm run dev`. This installs all dependencies including `vite`.

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
   
   **Note:** If you see `'vite' is not recognized`, it means dependencies aren't installed. Run `npm install` first.

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

## Troubleshooting

### YouTube Video Processing Issues

If you see warnings like "No supported JavaScript runtime could be found" when processing YouTube videos:

1. **Install Node.js 18+** from https://nodejs.org/
2. **Verify installation:**
   ```bash
   node --version  # Should show v18.0.0 or higher
   ```
3. **Restart your backend server** after installing Node.js

**Why is Node.js needed?** The `yt-dlp` library (used for downloading YouTube audio) requires a JavaScript runtime to extract some video formats. Without it, some videos may fail to process or certain formats may be skipped.
