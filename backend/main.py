"""
YouTube Knowledge Base - FastAPI Application
Main entry point for the backend server
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="YouTube Knowledge Base API",
    description="Extract, queue, and transcribe YouTube videos with speaker diarization",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Check if API is running"""
    return {
        "status": "healthy",
        "service": "youtube-knowledge-base-api",
        "version": "0.1.0"
    }


# Root endpoint
@app.get("/", tags=["Info"])
async def root():
    """Root endpoint"""
    return {
        "message": "YouTube Knowledge Base API",
        "docs": "/docs",
        "redoc": "/redoc",
        "version": "0.1.0"
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("🚀 YouTube Knowledge Base API starting up...")

    # Create required directories
    directories = [
        Path("/app/transcripts"),
        Path("/app/metadata"),
        Path("/app/metadata/channels"),
        Path("/app/metadata/playlists"),
        Path("/app/metadata/videos"),
        Path("/app/queue"),
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ Directory ready: {directory}")

    logger.info("✅ Startup complete")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 YouTube Knowledge Base API shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
