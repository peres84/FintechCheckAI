#!/usr/bin/env python3
"""
FinTech Check AI Backend Server - Main Entry Point

Run this file to start the backend server:
    python main.py

For development with auto-reload:
    python main.py --reload

For production:
    python main.py --port 8000
"""

import os
import sys
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    from backend.main import app
    import uvicorn
    from backend.core.config import config
    from backend.core.logging import log_handler
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="FinTech Check AI Backend Server")
    parser.add_argument("--host", type=str, default=None, help="Host to bind to (default: from config)")
    parser.add_argument("--port", type=int, default=None, help="Port to bind to (default: from config or PORT env var)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--workers", type=int, default=None, help="Number of worker processes (default: from config)")
    args = parser.parse_args()
    
    # Get configuration
    host = args.host or config["network"]["host"]
    port = args.port or int(os.getenv("PORT", config["network"]["server_port"]))
    reload = args.reload if args.reload else config["network"]["reload"]
    workers = args.workers if args.workers is not None else (config["network"]["workers"] if not reload else 1)
    
    # Log startup information
    log_handler.info("=" * 60)
    log_handler.info("FinTech Check AI Backend Server")
    log_handler.info("=" * 60)
    log_handler.info(f"Starting server at http://{host}:{port}")
    log_handler.info(f"API Documentation: http://{host}:{port}/docs")
    log_handler.info(f"Health Check: http://{host}:{port}/health")
    log_handler.info(f"Mode: {'Development' if reload else 'Production'}")
    if not reload:
        log_handler.info(f"Workers: {workers}")
    log_handler.info("=" * 60)
    
    try:
        uvicorn.run(
            "backend.main:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,
            proxy_headers=config["network"]["proxy_headers"],
            log_level="info"
        )
    except KeyboardInterrupt:
        log_handler.info("Server stopped by user")
    except Exception as e:
        log_handler.error(f"Server startup failed: {e}")
        sys.exit(1)
