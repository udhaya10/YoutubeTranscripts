"""
FastAPI routes for YouTube extraction and queue management
Implements M10-M13: Tree UI API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum
import re
import uuid
import logging

from backend.youtube_utils import YouTubeURLParser
from backend.youtube_extractor import YouTubeExtractor, ExtractionError, ErrorType
from backend.database import JobDatabase
from backend.metadata_store import MetadataStore

logger = logging.getLogger(__name__)

# Valid job status values
class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

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

    @validator('url')
    def validate_url(cls, v):
        if not v or len(v) > 2048:
            raise ValueError('URL must be between 1-2048 characters')
        if not v.startswith(('http://', 'https://', 'www.', 'youtube.')):
            raise ValueError('URL must be a valid YouTube URL')
        return v


class ExtractResponse(BaseModel):
    """Response from URL extraction"""
    type: str
    id: str
    title: Optional[str]
    metadata: Dict[str, Any]


class JobRequest(BaseModel):
    """Request to create job"""
    video_id: str = Field(..., min_length=1, max_length=100)
    video_title: Optional[str] = Field(None, max_length=1000)
    playlist_id: Optional[str] = Field(None, max_length=100)

    @validator('video_id')
    def validate_video_id(cls, v):
        # YouTube video IDs are 11 characters alphanumeric (including _ and -)
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Video ID must contain only alphanumeric characters, underscores, and hyphens')
        return v


class JobUpdateRequest(BaseModel):
    """Request to update job"""
    status: JobStatus
    progress: float = Field(0.0, ge=0.0, le=100.0)
    error_message: Optional[str] = Field(None, max_length=5000)

    @validator('progress')
    def validate_progress(cls, v, values):
        # Ensure progress is within bounds
        if not (0.0 <= v <= 100.0):
            raise ValueError('Progress must be between 0.0 and 100.0')
        return v


class AddToQueueRequest(BaseModel):
    """Request to add multiple videos to queue"""
    video_ids: List[str] = Field(..., min_items=1, max_items=1000)

    @validator('video_ids')
    def validate_video_ids(cls, v):
        if len(v) > 1000:
            raise ValueError('Cannot add more than 1000 videos at once')
        for video_id in v:
            if not isinstance(video_id, str) or not video_id:
                raise ValueError('All video IDs must be non-empty strings')
            if not re.match(r'^[a-zA-Z0-9_-]+$', video_id):
                raise ValueError(f'Invalid video ID format: {video_id}')
        return v


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
            result = extractor.extract_video(content_id)
        elif url_type == "playlist":
            result = extractor.extract_playlist(content_id)
        elif url_type == "channel":
            result = extractor.extract_channel(content_id)
        else:
            raise HTTPException(status_code=400, detail="Unable to determine URL type")

        # Handle extraction errors
        if isinstance(result, ExtractionError):
            if result.error_type == ErrorType.TIMEOUT:
                raise HTTPException(status_code=503, detail=f"Request timeout: {result.message}")
            elif result.error_type == ErrorType.NOT_FOUND:
                raise HTTPException(status_code=404, detail=f"Content not found: {result.message}")
            elif result.error_type == ErrorType.RATE_LIMITED:
                raise HTTPException(status_code=429, detail=f"Rate limited: {result.message}")
            elif result.error_type in (ErrorType.FORBIDDEN, ErrorType.RESTRICTED, ErrorType.PRIVATE):
                raise HTTPException(status_code=403, detail=f"Access forbidden: {result.message}")
            else:
                raise HTTPException(status_code=400, detail=f"Extraction failed: {result.message}")

        # Success path - result is a Dict
        metadata = result
        title = metadata.get("title", "Unknown Content")

        # Save metadata
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
async def update_job(job_id: str, request: JobUpdateRequest):
    """Update job status"""
    try:
        # Validate job_id format
        if not job_id or len(job_id) > 100:
            raise HTTPException(status_code=400, detail="Invalid job ID format")

        db = get_db()
        job = db.update_job_status(
            job_id,
            request.status.value,  # Convert enum to string value
            request.progress,
            error_message=request.error_message
        )

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return job

    except HTTPException:
        raise
    except ValueError as e:
        # Validation error from request model
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Job update error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/add-selected")
async def add_selected_to_queue(request: AddToQueueRequest):
    """Add selected videos to queue"""
    try:
        # Request validation is handled by Pydantic model
        created_jobs = []
        db = get_db()

        for video_id in request.video_ids:
            job_id = str(uuid.uuid4())
            job = db.create_job(job_id=job_id, video_id=video_id)
            created_jobs.append(job)

        return {
            "created": len(created_jobs),
            "jobs": created_jobs
        }

    except ValueError as e:
        # Validation error from request model
        raise HTTPException(status_code=422, detail=str(e))
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
