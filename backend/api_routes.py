"""
FastAPI routes for YouTube extraction and queue management
Implements M10-M13: Tree UI API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import logging

from youtube_utils import YouTubeURLParser
from youtube_extractor import YouTubeExtractor
from database import JobDatabase
from metadata_store import MetadataStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["YouTube"])

# Lazy initialization of services
_extractor = None
_db = None
_metadata_store = None


def get_extractor():
    """Get or initialize YouTubeExtractor"""
    global _extractor
    if _extractor is None:
        _extractor = YouTubeExtractor()
    return _extractor


def get_db():
    """Get or initialize JobDatabase"""
    global _db
    if _db is None:
        _db = JobDatabase()
    return _db


def get_metadata_store():
    """Get or initialize MetadataStore"""
    global _metadata_store
    if _metadata_store is None:
        _metadata_store = MetadataStore()
    return _metadata_store


# Request/Response models
class ExtractRequest(BaseModel):
    """Request to extract YouTube URL"""
    url: str


class ExtractResponse(BaseModel):
    """Response from URL extraction"""
    type: str
    id: str
    title: Optional[str]
    metadata: Dict[str, Any]


class JobRequest(BaseModel):
    """Request to create job"""
    video_id: str
    video_title: Optional[str] = None
    playlist_id: Optional[str] = None


# M10-M11: URL extraction endpoint
@router.post("/extract", response_model=ExtractResponse)
async def extract_url(request: ExtractRequest):
    """
    Extract YouTube URL and get metadata structure
    Returns channel/playlist/video hierarchy
    """
    try:
        # Parse URL
        parsed = YouTubeURLParser.parse_url(request.url)

        if not parsed["valid"]:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")

        url_type = parsed["type"]
        content_id = parsed.get("id")

        # Extract based on type
        extractor = get_extractor()
        if url_type == "video":
            metadata = extractor.extract_video(content_id) or {}
            title = metadata.get("title", "Unknown Video")
        elif url_type == "playlist":
            metadata = extractor.extract_playlist(content_id) or {}
            title = metadata.get("title", "Unknown Playlist")
        elif url_type == "channel":
            metadata = extractor.extract_channel(content_id) or {}
            title = metadata.get("title", "Unknown Channel")
        else:
            raise HTTPException(status_code=400, detail="Unable to determine URL type")

        # Save metadata
        if metadata:
            metadata_store = get_metadata_store()
            if url_type == "video":
                metadata_store.save_video_metadata(content_id, metadata)
            elif url_type == "playlist":
                metadata_store.save_playlist_metadata(content_id, metadata)
            elif url_type == "channel":
                metadata_store.save_channel_metadata(content_id, metadata)

        return ExtractResponse(
            type=url_type,
            id=content_id,
            title=title,
            metadata=metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extraction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# M12-M13: Queue management endpoints
@router.post("/jobs", response_model=Dict[str, Any])
async def create_job(request: JobRequest):
    """Create transcription job"""
    try:
        job_id = str(uuid.uuid4())
        db = get_db()

        job = db.create_job(
            job_id=job_id,
            video_id=request.video_id,
            video_title=request.video_title,
            playlist_id=request.playlist_id,
        )

        return job

    except Exception as e:
        logger.error(f"Job creation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def list_jobs(status: Optional[str] = None):
    """List jobs, optionally filtered by status"""
    try:
        db = get_db()
        if status:
            jobs = db.list_jobs(status=status)
        else:
            jobs = db.list_jobs()

        return {"jobs": jobs, "count": len(jobs)}

    except Exception as e:
        logger.error(f"Job listing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Get specific job"""
    try:
        db = get_db()
        job = db.read_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return job

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/jobs/{job_id}")
async def update_job(job_id: str, status: str, progress: float = 0.0):
    """Update job status"""
    try:
        db = get_db()
        job = db.update_job_status(job_id, status, progress)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return job

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job update error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/add-selected")
async def add_selected_to_queue(video_ids: List[str]):
    """Add selected videos to queue"""
    try:
        created_jobs = []
        db = get_db()

        for video_id in video_ids:
            job_id = str(uuid.uuid4())
            job = db.create_job(job_id=job_id, video_id=video_id)
            created_jobs.append(job)

        return {
            "created": len(created_jobs),
            "jobs": created_jobs
        }

    except Exception as e:
        logger.error(f"Add to queue error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metadata/channel/{channel_id}")
async def get_channel_metadata(channel_id: str):
    """Get cached channel metadata"""
    metadata_store = get_metadata_store()
    data = metadata_store.load_channel_metadata(channel_id)
    if not data:
        raise HTTPException(status_code=404, detail="Channel metadata not found")
    return data


@router.get("/metadata/playlist/{playlist_id}")
async def get_playlist_metadata(playlist_id: str):
    """Get cached playlist metadata"""
    metadata_store = get_metadata_store()
    data = metadata_store.load_playlist_metadata(playlist_id)
    if not data:
        raise HTTPException(status_code=404, detail="Playlist metadata not found")
    return data


@router.get("/metadata/video/{video_id}")
async def get_video_metadata(video_id: str):
    """Get cached video metadata"""
    metadata_store = get_metadata_store()
    data = metadata_store.load_video_metadata(video_id)
    if not data:
        raise HTTPException(status_code=404, detail="Video metadata not found")
    return data
