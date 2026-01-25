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


# Note: For production deployment, use the root-level main.py instead:
# python main.py --host 0.0.0.0 --port $PORT
#
# This file is kept for backward compatibility and direct uvicorn usage:
# uvicorn backend.main:app --reload
