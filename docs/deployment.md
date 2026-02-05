# Deployment Guide

Complete deployment instructions for FinTech Check AI platform.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Environment Configuration](#environment-configuration)
4. [Docker Deployment](#docker-deployment)
5. [Production Deployment](#production-deployment)
6. [Tower.dev Setup](#towerdev-setup)
7. [External Services Setup](#external-services-setup)
8. [Monitoring & Logging](#monitoring--logging)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Python 3.11+** - Backend runtime
- **Node.js 18+** - ⚠️ **REQUIRED** for both frontend and backend
  - **Frontend:** Build tool and development server
  - **Backend:** Required by `yt-dlp` for YouTube video extraction (when captions unavailable)
  - **Installation:** https://nodejs.org/ (LTS version recommended)
  - **Verify:** `node --version` should show v18.0.0 or higher
- **UV** - Python package manager (optional, pip works too)
- **Docker & Docker Compose** - Containerization (optional)
- **Git** - Version control

**⚠️ Important:** Without Node.js, YouTube video processing will fail with warnings about missing JavaScript runtime. Some videos may not be processable.

### Required Accounts & API Keys

- **OpenAI API Key** - For AI agent services
- **Tower.dev Account** - For document storage
- **RunPod Account** - For audio transcription (optional)
- **ImageKit Account** - For temporary file storage (optional)
- **Opik Account** - For observability (optional)

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd Fintech_CheckAI
```

### 2. Backend Setup

#### Option A: Using UV (Recommended)

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Unix/Mac:
source .venv/bin/activate

# Install UV
pip install uv

# Install backend dependencies
uv pip install -e ./backend
```

#### Option B: Using pip

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Unix/Mac

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
# or
bun install

# Start development server
npm run dev
# or
bun dev
```

### 4. Configure Environment

Create `.env` file in project root:

```bash
cp .env.example .env
```

Edit `.env` with your API keys (see [Environment Configuration](#environment-configuration)).

### 5. Start Backend Server

```bash
# From project root
python run_server.py

# Or using uvicorn directly
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### 6. Verify Installation

- Backend: http://127.0.0.1:8000/docs
- Frontend: http://localhost:5173 (Vite default)

---

## Environment Configuration

### Required Variables

```env
# OpenAI (Required for AI Agent)
OPENAI_API_KEY=sk-...

# Tower.dev (Required for document storage)
TOWER_API_KEY=...

# RunPod (Required for audio transcription fallback)
RUNPOD_API_KEY=...
RUNPOD_ENDPOINT_ID=...

# ImageKit (Required for temporary file storage)
IMAGEKIT_PRIVATE_KEY=...
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/your-id
```

### Optional Variables

```env
# Opik (Optional - for observability)
OPIK_API_KEY=...
OPIK_WORKSPACE=fintech-check-ai

# Server Configuration
PORT=8000
APP_ENV=development
```

### Getting API Keys

1. **OpenAI**: https://platform.openai.com/api-keys
2. **Tower.dev**: https://app.tower.dev/settings/api-keys
3. **RunPod**: https://www.runpod.io/console/user/settings
4. **ImageKit**: https://imagekit.io/dashboard/developer/api-keys
5. **Opik**: https://opik.ai/settings/api-keys

---

## Docker Deployment

### Using Docker Compose

#### 1. Build and Start Services

```bash
# From project root
docker-compose up -d
```

#### 2. View Logs

```bash
docker-compose logs -f backend
```

#### 3. Stop Services

```bash
docker-compose down
```

### Dockerfile Details

**Backend Dockerfile:** `backend/DOCKERFILE`

**Build Command:**
```bash
cd backend
docker build -f DOCKERFILE -t fintech-check-ai-backend .
```

**Run Container:**
```bash
docker run -p 8000:8000 --env-file .env fintech-check-ai-backend
```

### Docker Compose Configuration

**File:** `docker-compose.yml`

Services:
- `backend`: FastAPI application
- `frontend`: React application (if needed)
- Additional services can be added (Redis, PostgreSQL, etc.)

---

## Production Deployment

### Option 1: Cloud Platform (Recommended)

#### Railway

1. Connect GitHub repository
2. Set environment variables
3. Deploy automatically on push

#### Render

1. Create new Web Service
2. Connect repository
3. Set build command: `pip install -r backend/requirements.txt`
4. Set start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables

#### AWS/GCP/Azure

Use containerized deployment:
- AWS: ECS, EKS, or Elastic Beanstalk
- GCP: Cloud Run, GKE
- Azure: Container Instances, AKS

### Option 2: VPS Deployment

#### Using Systemd

1. **Create service file:** `/etc/systemd/system/fintech-check-ai.service`

```ini
[Unit]
Description=FinTech Check AI Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/fintech-check-ai
Environment="PATH=/opt/fintech-check-ai/.venv/bin"
ExecStart=/opt/fintech-check-ai/.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

2. **Enable and start:**
```bash
sudo systemctl enable fintech-check-ai
sudo systemctl start fintech-check-ai
```

3. **Check status:**
```bash
sudo systemctl status fintech-check-ai
```

#### Using Nginx Reverse Proxy

**Nginx configuration:** `/etc/nginx/sites-available/fintech-check-ai`

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/fintech-check-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL/TLS Setup

Use Let's Encrypt with Certbot:

```bash
sudo certbot --nginx -d api.yourdomain.com
```

---

## Tower.dev Setup

### 1. Install Tower CLI

```bash
pip install tower-cli
# or
uv pip install tower-cli
```

### 2. Authenticate

```bash
tower login
```

Enter your Tower.dev credentials.

### 3. Select Team/Workspace

```bash
tower workspace select <workspace-name>
```

### 4. Create Schemas

Schemas are already defined in `backend/tower/schemas/`:

- `companies.sql`
- `documents.sql`
- `chunks.sql`
- `verifications.sql`

### 5. Run Tower Apps

See `docs/TOWER_RUNBOOK.md` for detailed instructions.

**Quick Start:**
```bash
# Document ingestion
cd backend/tower/apps/document-ingestion
tower run --environment=default \
  --parameter=PDF_URL="https://example.com/doc.pdf" \
  --parameter=COMPANY_ID="duolingo" \
  --parameter=VERSION="v1"

# Chunk storage
cd backend/tower/apps/chunk-storage
tower run --environment=default \
  --parameter=DOCUMENT_ID="<document-id>" \
  --parameter=CHUNKS_URL="https://example.com/chunks.json"
```

---

## External Services Setup

### RunPod Setup

1. **Create Endpoint:**
   - Go to RunPod console
   - Create new endpoint
   - Select Whisper model
   - Note endpoint ID

2. **Configure:**
   ```env
   RUNPOD_API_KEY=your-api-key
   RUNPOD_ENDPOINT_ID=your-endpoint-id
   ```

### ImageKit Setup

1. **Create Account:** https://imagekit.io
2. **Get Credentials:**
   - Private Key: Dashboard → Developer Options
   - URL Endpoint: Dashboard → URLs

3. **Configure:**
   ```env
   IMAGEKIT_PRIVATE_KEY=your-private-key
   IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/your-id
   ```

### Opik Setup

1. **Create Account:** https://opik.ai
2. **Create Workspace:**
   - Name: `fintech-check-ai`
   - Note API key

3. **Configure:**
   ```env
   OPIK_API_KEY=your-api-key
   OPIK_WORKSPACE=fintech-check-ai
   ```

---

## Monitoring & Logging

### Log Files

**Location:** `logs/` directory (created automatically)

**Format:** `fintech_check_ai_YYYY-MM-DDTHH-MM-SS.log`

**Log Levels:**
- `DEBUG`: Detailed debugging information
- `INFO`: General informational messages
- `WARNING`: Warning messages
- `ERROR`: Error messages

### Health Checks

Monitor these endpoints:

- `GET /health` - Overall API health
- `GET /api/youtube/health` - YouTube service
- `GET /api/ai-agent/health` - AI Agent service

### Opik Dashboard

Access Opik dashboard for:
- Agent execution traces
- LLM call tracking
- Performance metrics
- Error analysis

**URL:** https://opik.ai/workspace/fintech-check-ai

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem:** `ModuleNotFoundError` when running server

**Solution:**
```bash
# Ensure you're in project root
cd /path/to/Fintech_CheckAI

# Activate virtual environment
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Reinstall dependencies
uv pip install -e ./backend
```

#### 2. Port Already in Use

**Problem:** `Address already in use` error

**Solution:**
```bash
# Find process using port 8000
# Windows:
netstat -ano | findstr :8000
# Unix/Mac:
lsof -i :8000

# Kill process or change port in config.json
```

#### 3. Missing Environment Variables

**Problem:** `RuntimeError: OPENAI_API_KEY not set`

**Solution:**
- Check `.env` file exists in project root
- Verify all required variables are set
- Restart server after adding variables

#### 4. Tower Connection Issues

**Problem:** `Tower SDK unavailable` or connection errors

**Solution:**
```bash
# Re-authenticate
tower login

# Verify workspace
tower workspace list

# Check API key in .env
TOWER_API_KEY=your-key
```

#### 5. RunPod Transcription Fails

**Problem:** Audio transcription returns errors

**Solution:**
- Verify `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID` are correct
- Check RunPod endpoint is active
- Verify ImageKit credentials for temporary storage

#### 6. Frontend Can't Connect to Backend

**Problem:** CORS errors or connection refused

**Solution:**
- Verify backend is running on correct port
- Check `VITE_API_BASE_URL` in frontend `.env`
- Add CORS middleware if needed (see FastAPI docs)

#### 7. YouTube Video Processing Warnings/Failures

**Problem:** Warnings about "No supported JavaScript runtime" or videos failing to process

**Solution:**
- **Install Node.js 18+** from https://nodejs.org/
- Verify installation: `node --version` (should show v18+)
- Restart backend server after installing Node.js
- Node.js is required for `yt-dlp` to extract YouTube videos when captions are unavailable
- Without Node.js, some video formats may be skipped and processing may fail

### Debug Mode

Enable debug logging:

**config.json:**
```json
{
  "logging": {
    "logging_level": "debug"
  }
}
```

### Getting Help

1. Check logs in `logs/` directory
2. Review error messages in API responses
3. Check Opik dashboard for agent traces
4. Review GitHub issues
5. Contact support

---

## Backup & Recovery

### Database Backup

Tower.dev handles backups automatically. For manual backup:

```bash
# Export data (if Tower CLI supports it)
tower export --table documents --output documents_backup.json
```

### Configuration Backup

Backup these files:
- `.env` (securely, without committing)
- `backend/core/config.json`
- `backend/tower/schemas/*.sql`

### Recovery Procedure

1. Restore environment variables
2. Restore configuration files
3. Re-run Tower schema creation if needed
4. Restart services

---

## Scaling Considerations

### Horizontal Scaling

1. **Load Balancer:** Add Nginx/HAProxy in front
2. **Multiple Workers:** Use `--workers` flag with uvicorn
3. **Task Queue:** Add Celery/RQ for async processing
4. **Caching:** Add Redis for transcript/claim caching

### Vertical Scaling

1. Increase server resources (CPU, RAM)
2. Use faster AI models (gpt-4o instead of gpt-4o-mini)
3. Optimize database queries

---

## Security Checklist

- [ ] All API keys stored in environment variables
- [ ] `.env` file in `.gitignore`
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] HTTPS enabled in production
- [ ] CORS configured properly
- [ ] Error messages don't expose sensitive data
- [ ] Logs don't contain API keys
- [ ] Regular dependency updates
- [ ] Security headers configured

---

*Last Updated: 2026-01-25*
