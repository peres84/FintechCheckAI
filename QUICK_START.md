# Quick Start Guide

Get FinTech Check AI running locally in minutes!

## Prerequisites

- **Python 3.11+** installed
- **Node.js 18+** and npm installed ⚠️ **REQUIRED** - Without Node.js, YouTube video processing will fail
- API keys (see below)

### Installing Node.js

**⚠️ Node.js is REQUIRED for the backend to work properly!**

Node.js is needed for `yt-dlp` to extract YouTube videos when captions are unavailable. Without it, you'll see warnings and video processing may fail.

**Installation:**
- **Windows/Mac:** Download LTS version from https://nodejs.org/
- **Linux:** 
  ```bash
  # Ubuntu/Debian
  sudo apt update && sudo apt install nodejs npm
  
  # Or use nvm (recommended)
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
  nvm install 18
  ```

**Verify installation:**
```bash
node --version  # Should show v18.0.0 or higher
npm --version   # Should show 9.0.0 or higher
```

## Step 1: Clone and Setup

```bash
git clone <your-repo-url>
cd Fintech_CheckAI
```

## Step 2: Backend Setup

### Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
# Minimum required:
# - OPENAI_API_KEY
# - RUNPOD_API_KEY
# - RUNPOD_ENDPOINT_ID
# - IMAGEKIT_PRIVATE_KEY
# - IMAGEKIT_URL_ENDPOINT
```

### Start Backend

**You can run from either location:**

**Option 1: From project root (RECOMMENDED):**
```bash
# Make sure you're in the project root (where main.py is)
# You should see: main.py, backend/, frontend/, README.md

python main.py
```

**Option 2: From backend directory (also works):**
```bash
cd backend
python main.py
```

**That's it!** The backend will start at `http://127.0.0.1:8000`

- API Docs: http://127.0.0.1:8000/docs
- Health Check: http://127.0.0.1:8000/health

For development with auto-reload:
```bash
# From project root
python main.py --reload

# Or from backend directory
cd backend
python main.py  # Auto-reload is enabled by default
```

**Note:** Warnings about `fitz` (PDF processor) and `opik` are normal - these are optional dependencies.

## Step 3: Frontend Setup

### Install Dependencies

**⚠️ IMPORTANT: Run `npm install` first!**

```bash
cd frontend
npm install
```

This installs all dependencies including `vite`. You must run this before `npm run dev`.

### Configure Environment (Optional)

```bash
# Copy example environment file
cp .env.example .env

# Edit .env if backend is on different URL
# Default: VITE_API_BASE_URL=http://127.0.0.1:8000
```

### Start Frontend

```bash
npm run dev
```

**That's it!** The frontend will start at `http://localhost:8080`

## Step 4: Test It!

1. Open http://localhost:8080 in your browser
2. Select a company from the dropdown
3. Enter a YouTube URL
4. Click "Start Analysis"
5. Wait for results!

## Common Mistakes

### ❌ Running Backend from Wrong Directory

```bash
# WRONG - Don't do this!
cd backend
python main.py  # ❌ This won't work correctly
```

```bash
# CORRECT - Do this!
# From project root (where main.py is located)
python main.py  # ✅ This works!
```

### ❌ Running Frontend Without Installing Dependencies

```bash
# WRONG - Don't do this!
cd frontend
npm run dev  # ❌ Error: 'vite' is not recognized
```

```bash
# CORRECT - Do this!
cd frontend
npm install  # ✅ Install dependencies first
npm run dev  # ✅ Now this works!
```

## Troubleshooting

### Backend won't start

- **Port already in use?** Change port: `python main.py --port 8001`
- **Missing dependencies?** Run: `pip install -r backend/requirements.txt`
- **Import errors?** Make sure you're running from project root (where `main.py` is)
- **Running from backend/ directory?** Go back to project root: `cd ..`

### Frontend won't start

- **Port already in use?** Vite will automatically use next available port
- **Missing dependencies?** Run: `npm install` (you must do this first!)
- **API errors?** Check that backend is running and `VITE_API_BASE_URL` is correct
- **'vite' not recognized?** Run `npm install` first!

### CORS Errors

- Backend CORS is configured for `localhost:8080` by default
- If using different port, add it to `CORS_ORIGINS` in `.env`

## Directory Structure

```
Fintech_CheckAI/          ← Project root (run python main.py from here)
├── main.py              ← Backend entry point (run this!)
├── backend/
│   ├── main.py          ← FastAPI app (don't run this directly)
│   ├── api/
│   ├── services/
│   └── ...
├── frontend/
│   ├── package.json
│   └── ...
└── README.md
```

## Next Steps

- Read [README.md](README.md) for more details
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- See [docs/](docs/) for architecture and API documentation

---

**Happy fact-checking!** 🎉
