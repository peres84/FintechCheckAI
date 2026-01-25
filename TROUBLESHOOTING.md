# Troubleshooting Guide

Common issues and solutions for FinTech Check AI.

## Frontend Issues

### "vite is not recognized" Error

**Error:**
```
'vite' is not recognized as an internal or external command,
operable program or batch file.
```

**Solution:**
```bash
cd frontend
npm install
```

This installs all dependencies including `vite`. You must run `npm install` before `npm run dev`.

**Why it happens:**
- `node_modules` directory doesn't exist
- Dependencies haven't been installed
- `package.json` exists but packages aren't installed

---

### Frontend Build Fails

**Error:**
```
Module not found: Can't resolve '@/...'
```

**Solution:**
1. Check that `vite.config.ts` has the correct alias:
   ```typescript
   resolve: {
     alias: {
       "@": path.resolve(__dirname, "./src"),
     },
   }
   ```

2. Verify TypeScript paths in `tsconfig.json`:
   ```json
   {
     "compilerOptions": {
       "paths": {
         "@/*": ["./src/*"]
       }
     }
   }
   ```

3. Restart the dev server after changes

---

### API Calls Failing (CORS Errors)

**Error:**
```
Access to fetch at 'http://127.0.0.1:8000/...' from origin 'http://localhost:8080' 
has been blocked by CORS policy
```

**Solution:**
1. Check backend CORS configuration in `backend/main.py`
2. Ensure `CORS_ORIGINS` includes your frontend URL:
   ```bash
   CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
   ```
3. Restart backend after changing CORS settings

---

### Frontend Can't Connect to Backend

**Error:**
```
Failed to fetch
Network error
```

**Solution:**
1. Verify backend is running:
   ```bash
   curl http://127.0.0.1:8000/health
   ```

2. Check `VITE_API_BASE_URL` in `frontend/.env`:
   ```bash
   VITE_API_BASE_URL=http://127.0.0.1:8000
   ```

3. Restart frontend dev server after changing `.env`

4. Check browser console for detailed error messages

---

## Backend Issues

### "Module not found" Errors

**Error:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
pip install -r backend/requirements.txt
```

Or if using a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
pip install -r backend/requirements.txt
```

---

### Port Already in Use

**Error:**
```
Address already in use
Port 8000 is already in use
```

**Solution:**
1. **Find and kill the process:**
   ```bash
   # Windows
   netstat -ano | findstr :8000
   taskkill /PID <PID> /F
   
   # Linux/Mac
   lsof -ti:8000 | xargs kill
   ```

2. **Or use a different port:**
   ```bash
   python main.py --port 8001
   ```

3. **Update frontend API URL:**
   ```bash
   # frontend/.env
   VITE_API_BASE_URL=http://127.0.0.1:8001
   ```

---

### Environment Variables Not Loading

**Error:**
```
RuntimeError: Missing required environment variable: OPENAI_API_KEY
```

**Solution:**
1. Create `.env` file in project root:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```bash
   OPENAI_API_KEY=sk-...
   RUNPOD_API_KEY=...
   # etc.
   ```

3. Verify `.env` is in project root (not in `backend/` or `frontend/`)

4. Restart the backend server

---

### Import Errors (Backend)

**Error:**
```
ImportError: cannot import name 'app' from 'backend.main'
ModuleNotFoundError: No module named 'backend'
```

**Solution:**
1. **Make sure you're running from project root (NOT from backend/):**
   ```bash
   # Correct - from project root
   cd C:\Users\Acer\Documents\GitHub\Fintech_CheckAI
   python main.py
   
   # Wrong - from backend directory
   cd backend
   python main.py  # ❌ This won't work correctly
   ```

2. **Verify you're in the right directory:**
   ```bash
   # Should show: main.py, backend/, frontend/, README.md
   dir
   
   # If you see: main.py, api/, services/, etc. - you're in backend/ (wrong!)
   ```

3. **Check `PYTHONPATH` if issues persist:**
   ```bash
   # Windows
   set PYTHONPATH=%CD%
   
   # Linux/Mac
   export PYTHONPATH=$PWD
   ```

### Running from Wrong Directory

**Symptom:**
- Server appears to start but doesn't actually run
- Import errors
- Path-related errors
- Logs show warnings but server doesn't start

**Solution:**
Always run `python main.py` from the project root directory where `main.py` is located, not from `backend/` directory.

---

## Docker Issues

### Docker Build Fails

**Error:**
```
ERROR: failed to solve: process "/bin/sh -c pip install..." did not complete successfully
```

**Solution:**
1. Check `backend/requirements.txt` syntax
2. Verify Python version in Dockerfile (3.11)
3. Try rebuilding without cache:
   ```bash
   docker-compose build --no-cache
   ```

---

### Container Won't Start

**Error:**
```
Container exited with code 1
```

**Solution:**
1. Check logs:
   ```bash
   docker-compose logs backend
   ```

2. Verify environment variables are set:
   ```bash
   docker-compose config
   ```

3. Test container manually:
   ```bash
   docker run -it --env-file .env fintech-backend /bin/bash
   ```

---

### Port Conflicts in Docker

**Error:**
```
Bind for 0.0.0.0:8000 failed: port is already allocated
```

**Solution:**
1. Stop existing containers:
   ```bash
   docker-compose down
   ```

2. Check for running containers:
   ```bash
   docker ps
   ```

3. Change port in `docker-compose.yml`:
   ```yaml
   ports:
     - "8001:8000"  # Host:Container
   ```

---

## General Issues

### Python Version Issues

**Error:**
```
Python 3.11+ is required
```

**Solution:**
1. Check Python version:
   ```bash
   python --version
   ```

2. Install Python 3.11+ if needed:
   - Download from https://www.python.org/downloads/
   - Or use pyenv: `pyenv install 3.11.0`

---

### Node.js Version Issues

**Error:**
```
The engine "node" is incompatible with this module
```

**Solution:**
1. Check Node.js version:
   ```bash
   node --version
   ```

2. Install Node.js 18+ if needed:
   - Download from https://nodejs.org/
   - Or use nvm: `nvm install 18`

---

### Git Issues

**Error:**
```
fatal: not a git repository
```

**Solution:**
If you cloned without `.git`, initialize:
```bash
git init
git remote add origin <your-repo-url>
```

---

## Still Having Issues?

1. **Check logs:**
   - Backend: `logs/fintech_check_ai_*.log`
   - Frontend: Browser console
   - Docker: `docker-compose logs`

2. **Verify installation:**
   - Backend: `python -c "from backend.main import app; print('OK')"`
   - Frontend: `cd frontend && npm list vite`

3. **Clean and reinstall:**
   ```bash
   # Backend
   pip uninstall -r backend/requirements.txt -y
   pip install -r backend/requirements.txt
   
   # Frontend
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

4. **Check documentation:**
   - [README.md](README.md)
   - [DOCKER_SETUP.md](DOCKER_SETUP.md)
   - [docs/](docs/)

---

*Last Updated: 2026-01-25*
