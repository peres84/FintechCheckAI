#!/usr/bin/env python3
"""
FinTech Check AI Backend Server Startup Script

This script starts the FastAPI backend server with proper configuration.
Run this script to start the development server.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the backend
if __name__ == "__main__":
    from backend.main import app, config, log_handler
    import uvicorn
    
    port = int(os.getenv("PORT", config["network"]["server_port"]))
    host = config["network"]["host"]
    
    log_handler.info("=" * 50)
    log_handler.info("FinTech Check AI Backend Server")
    log_handler.info("=" * 50)
    log_handler.info(f"Starting server at http://{host}:{port}")
    log_handler.info(f"API Documentation: http://{host}:{port}/docs")
    log_handler.info(f"Health Check: http://{host}:{port}/health")
    log_handler.info("=" * 50)
    
    try:
        uvicorn.run(
            "backend.main:app",
            host=host,
            port=port,
            reload=config["network"]["reload"],
            workers=1,  # Always 1 for development with reload
            proxy_headers=config["network"]["proxy_headers"],
            log_level="info"
        )
    except KeyboardInterrupt:
        log_handler.info("Server stopped by user")
    except Exception as e:
        log_handler.error(f"Server startup failed: {e}")
        sys.exit(1)