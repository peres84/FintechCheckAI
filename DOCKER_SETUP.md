# Docker Setup Guide

This guide covers building and running FinTech Check AI with Docker.

## Quick Start

### Backend Only

```bash
# Build and run backend
docker-compose up backend

# Or using the backend-specific compose file
cd backend
docker-compose up
```

### Full Stack (Backend + Frontend)

```bash
# From project root
docker-compose up
```

This will start both backend and frontend services.

## Building Images

### Backend

```bash
# Build backend image
docker build -f backend/Dockerfile -t fintech-check-ai-backend .

# Or using docker-compose
docker-compose build backend
```

### Frontend

```bash
# Build frontend image
docker build -f frontend/Dockerfile -t fintech-check-ai-frontend ./frontend

# Or using docker-compose
docker-compose build frontend
```

## Running Containers

### Backend

```bash
# Run backend container
docker run -d \
  --name fintech-backend \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -e RUNPOD_API_KEY=your_key \
  -e RUNPOD_ENDPOINT_ID=your_id \
  -e IMAGEKIT_PRIVATE_KEY=your_key \
  -e IMAGEKIT_URL_ENDPOINT=your_endpoint \
  fintech-check-ai-backend
```

### Frontend

```bash
# Run frontend container
docker run -d \
  --name fintech-frontend \
  -p 8080:80 \
  -e VITE_API_BASE_URL=http://localhost:8000 \
  fintech-check-ai-frontend
```

## Docker Compose

### Environment Variables

Create a `.env` file in the project root:

```bash
# Backend
OPENAI_API_KEY=sk-...
RUNPOD_API_KEY=...
RUNPOD_ENDPOINT_ID=...
IMAGEKIT_PRIVATE_KEY=...
IMAGEKIT_URL_ENDPOINT=...
TOWER_API_KEY=... (optional)
OPIK_API_KEY=... (optional)
CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080

# Ports
BACKEND_PORT=8000
FRONTEND_PORT=8080

# Frontend
VITE_API_BASE_URL=http://localhost:8000
```

### Commands

```bash
# Start all services
docker-compose up

# Start in detached mode
docker-compose up -d

# Stop all services
docker-compose down

# Rebuild and start
docker-compose up --build

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop and remove volumes
docker-compose down -v
```

## Dockerfile Details

### Backend Dockerfile

- **Base Image:** `python:3.11-slim`
- **Working Directory:** `/app`
- **Port:** 8000 (configurable via PORT env var)
- **Health Check:** `/health` endpoint
- **Command:** `python main.py --host 0.0.0.0 --port ${PORT:-8000}`

### Frontend Dockerfile

- **Build Stage:** Node.js 18 Alpine
- **Production Stage:** Nginx Alpine
- **Port:** 80 (mapped to 8080 in compose)
- **Static Files:** Served via Nginx with SPA routing

## Volumes

The docker-compose files mount:
- `./logs` - Backend logs directory
- `./temp_pdfs` - Temporary PDF storage

## Health Checks

Both services include health checks:
- **Backend:** `curl http://localhost:8000/health`
- **Frontend:** `curl http://localhost:8080/health`

## Troubleshooting

### Backend Issues

**Container won't start:**
```bash
# Check logs
docker-compose logs backend

# Check if port is in use
docker ps | grep 8000
```

**Import errors:**
```bash
# Rebuild image
docker-compose build --no-cache backend
```

**Environment variables not loading:**
- Ensure `.env` file exists in project root
- Check variables are set in docker-compose.yml

### Frontend Issues

**Build fails:**
```bash
# Check build logs
docker-compose logs frontend

# Rebuild without cache
docker-compose build --no-cache frontend
```

**API calls failing:**
- Verify `VITE_API_BASE_URL` is set correctly
- Check backend is accessible from frontend container
- Ensure CORS is configured on backend

### General Issues

**Port conflicts:**
```bash
# Change ports in docker-compose.yml or .env
BACKEND_PORT=8001
FRONTEND_PORT=8081
```

**Clean rebuild:**
```bash
# Remove all containers and images
docker-compose down -v
docker system prune -a

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up
```

## Production Deployment

### Backend

For production, use:
```bash
docker build -f backend/Dockerfile -t fintech-backend:latest .
docker run -d \
  --name fintech-backend \
  -p 8000:8000 \
  --env-file .env.production \
  --restart unless-stopped \
  fintech-backend:latest
```

### Frontend

For production, ensure `VITE_API_BASE_URL` points to your production backend:
```bash
docker build -f frontend/Dockerfile \
  --build-arg VITE_API_BASE_URL=https://api.yourdomain.com \
  -t fintech-frontend:latest \
  ./frontend
```

## Multi-Stage Build Benefits

- **Smaller Images:** Only production dependencies included
- **Faster Builds:** Layer caching for dependencies
- **Security:** Minimal attack surface with slim base images

## Best Practices

1. **Never commit `.env` files** - Use environment variables or secrets management
2. **Use specific tags** - Avoid `latest` in production
3. **Health checks** - Monitor container health
4. **Resource limits** - Set memory/CPU limits in production
5. **Logging** - Mount log directories for persistence
6. **Security** - Keep base images updated
7. **Multi-stage builds** - Reduce final image size

---

*Last Updated: 2026-01-25*
