"""
YouTube Knowledge Base - FastAPI Application
Main entry point for the backend server
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
from pathlib import Path
import os
import asyncio

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

# Import API routes and register router
from backend.api_routes import router as api_router
from backend.websocket_manager import ConnectionManager

# Import worker (deferred to avoid circular imports)
# from backend.worker import BackgroundWorker

# Global instances
ws_manager = ConnectionManager()
worker = None

# Register API router
app.include_router(api_router)

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

    # Start background worker (M18-M19)
    try:
        from backend.worker import BackgroundWorker
        from backend.database import JobDatabase
        from youtube_extractor import YouTubeExtractor

        global worker
        db = JobDatabase()
        extractor = YouTubeExtractor(
            output_dir="/app/transcripts",
            hf_token=os.getenv("HF_TOKEN")
        )
        worker = BackgroundWorker(db, extractor, ws_manager)
        await worker.start()
        logger.info("✓ Background worker started")
    except Exception as e:
        logger.error(f"Failed to start background worker: {e}")

    logger.info("✅ Startup complete")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 YouTube Knowledge Base API shutting down...")

    # Stop background worker
    global worker
    if worker:
        await worker.stop()
        logger.info("✓ Background worker stopped")

    # Close all WebSocket connections
    for ws in ws_manager.active_connections[:]:
        await ws.close()
    logger.info("✓ WebSocket connections closed")


# WebSocket endpoint for real-time queue updates (M19)
@app.websocket("/ws/queue")
async def websocket_queue(websocket: WebSocket):
    """WebSocket endpoint for real-time job queue updates"""
    await ws_manager.connect(websocket)
    try:
        # Keep connection alive with periodic heartbeats
        while True:
            # Send heartbeat every 30 seconds to detect disconnections
            await asyncio.sleep(30)
            try:
                await websocket.send_json({"type": "heartbeat"})
            except Exception:
                # Connection lost, will be handled by onclose
                break
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
