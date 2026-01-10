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
    
    # Import models to ensure tables are registered with Base.metadata
    from app import models  # noqa
    
    # Log config (careful to mask secrets)
    safe_db_url = settings.database_url.replace(
        settings.database_url.split("@")[0].split("//")[1].split(":")[1], 
        "******"
    ) if "@" in settings.database_url and ":" in settings.database_url.split("@")[0] else "Unknown"
    
    logger.info(f"Connecting to Database: {safe_db_url}")
    logger.info(f"Connecting to Redis: {settings.redis_url}")

    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # We don't raise here so the app can start and show health check errors
        # In production this might be bad, but for debugging deployment it's crucial
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    try:
        lock_manager = get_lock_manager()
        await lock_manager.close()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis connection: {e}")


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

# Redirect www to root domain and redirect root domain to www
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

class RedirectWWWMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """Redirect booknhost.info to www.booknhost.info"""
        host = request.headers.get("host", "")
        # Redirect root domain to www subdomain
        if host == "booknhost.info":
            # Preserve the path and query string
            url = request.url.replace(netloc="www.booknhost.info")
            return RedirectResponse(url=url, status_code=301)
        return await call_next(request)

app.add_middleware(RedirectWWWMiddleware)

# Include API routes
# Include API routes
app.include_router(api_router)


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
