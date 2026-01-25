import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Always add project root to path for consistent imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

# Import with absolute paths
from backend.core.logging import log_handler
from backend.core.config import config
from backend.api.routes import documents, verification, youtube, ai_agent, companies, version_diff
from backend.api.middleware.rate_limit import setup_rate_limiting

@asynccontextmanager
async def lifespan(app: FastAPI):
    port = os.getenv("PORT", config["network"]["server_port"])
    log_handler.info(f"FinTech Check AI backend server starting on port {port}")
    yield
    log_handler.info("FinTech Check AI backend server shutting down")

app = FastAPI(
    title="FinTech Check AI", 
    version="0.1.0",
    description="AI-powered financial document verification and analysis",
    lifespan=lifespan
)

# Add CORS middleware (before routers)
# Include common development ports: Vite (5173), React (3000), Next.js (3000), Vue (8080)
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080,http://127.0.0.1:8080,http://localhost:5174,http://127.0.0.1:5174"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup rate limiting (before routers)
setup_rate_limiting(app)

# Include routers
app.include_router(youtube.router, prefix="/api/youtube", tags=["youtube"])
app.include_router(ai_agent.router, prefix="/api/ai-agent", tags=["ai-agent"])
app.include_router(verification.router, prefix="/api", tags=["verification"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(companies.router, prefix="/api", tags=["companies"])
app.include_router(version_diff.router, prefix="/api", tags=["version-diff"])


@app.get("/health")
def health() -> dict:
    """Health check endpoint to verify the API is operational."""
    log_handler.debug("Health check endpoint accessed")
    return {"status": "ok", "service": "FinTech Check AI"}


# Server startup (for direct execution)
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", config["network"]["server_port"]))
    host = config["network"]["host"]
    
    log_handler.info("=" * 60)
    log_handler.info("FinTech Check AI Backend Server")
    log_handler.info("=" * 60)
    log_handler.info(f"Starting server at http://{host}:{port}")
    log_handler.info(f"API Documentation: http://{host}:{port}/docs")
    log_handler.info(f"Health Check: http://{host}:{port}/health")
    log_handler.info("=" * 60)
    log_handler.warning("NOTE: For best results, run 'python main.py' from project root instead!")
    log_handler.info("=" * 60)
    
    try:
        # Use import string for reload/workers support
        if config["network"]["reload"]:
            uvicorn.run(
                "backend.main:app",  # Import string for reload support
                host=host,
                port=port,
                reload=True,
                workers=1,  # Must be 1 when reload=True
                proxy_headers=config["network"]["proxy_headers"],
                log_level="info"
            )
        else:
            uvicorn.run(
                app,  # Can use app object when reload=False
                host=host,
                port=port,
                reload=False,
                workers=config["network"]["workers"],
                proxy_headers=config["network"]["proxy_headers"],
                log_level="info"
            )
    except KeyboardInterrupt:
        log_handler.info("Server stopped by user")
    except Exception as e:
        log_handler.error(f"Server startup failed: {e}")
        sys.exit(1)
