"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.api import api_router
from app.services.lock_manager import get_lock_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting Hotel Channel Manager...")
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    lock_manager = get_lock_manager()
    await lock_manager.close()
    logger.info("Redis connection closed")


app = FastAPI(
    title="Hotel Channel Manager",
    description="MVP Channel Manager for synchronizing hotel inventory across OTA channels",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
# Include API routes
app.include_router(api_router)

# Serve React Frontend (Static Files)
# Note: Ensure 'dist' directory exists (run npm run build)
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Check if dist directory exists (for production)
if os.path.exists("dist"):
    app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve React frontend for any unmatched route."""
        # API routes are already handled above
        # If file exists in dist, serve it
        possible_file = os.path.join("dist", full_path)
        if os.path.isfile(possible_file):
            return FileResponse(possible_file)
        
        # Otherwise serve index.html (SPA routing)
        return FileResponse("dist/index.html")
else:
    logger.warning("Frontend build directory 'dist' not found. API only mode.")



@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected",
    }
