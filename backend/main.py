import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
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
from backend.api.routes import documents, verification, youtube

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
app.include_router(verification.router, prefix="/api", tags=["verification"])
app.include_router(documents.router, prefix="/api", tags=["documents"])


@app.get("/health")
def health() -> dict:
    """Health check endpoint to verify the API is operational."""
    log_handler.debug("Health check endpoint accessed")
    return {"status": "ok", "service": "FinTech Check AI"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", config["network"]["server_port"]))
    log_handler.info(f"Starting server with configuration: host={config['network']['host']}, port={port}")
    
    uvicorn.run(
        config["network"]["uvicorn_app_reference"], 
        host=config["network"]["host"], 
        port=port, 
        reload=config["network"]["reload"],
        workers=config["network"]["workers"] if not config["network"]["reload"] else 1,  # Workers must be 1 when reload=True
        proxy_headers=config["network"]["proxy_headers"]
    )
