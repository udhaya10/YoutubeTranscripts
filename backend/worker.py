"""
Background job processor for automatic video transcription
Implements M18: Background job processing with queue management
"""
import asyncio
import logging
from typing import Optional

from database import JobDatabase
from youtube_extractor import YouTubeExtractor
from websocket_manager import ConnectionManager

logger = logging.getLogger(__name__)


class BackgroundWorker:
    """Processes pending jobs from queue in background with real-time progress updates"""

    def __init__(
        self,
        db: JobDatabase,
        extractor: YouTubeExtractor,
        ws_manager: ConnectionManager
    ):
        """
        Initialize background worker

        Args:
            db: JobDatabase instance for job queue management
            extractor: YouTubeExtractor instance for transcription
            ws_manager: ConnectionManager for broadcasting updates
        """
        self.db = db
        self.extractor = extractor
        self.ws_manager = ws_manager
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.current_job_id: Optional[str] = None

    async def start(self):
        """Start background processing loop"""
        self.running = True
        self.task = asyncio.create_task(self._process_loop())
        logger.info("Background worker started")

    async def stop(self):
        """Stop background processing gracefully"""
        logger.info("Stopping background worker...")
        self.running = False
        if self.task:
            await self.task
        logger.info("Background worker stopped")

    async def _process_loop(self):
        """
        Main processing loop that continuously processes pending jobs
        FIFO order by creation timestamp
        """
        while self.running:
            try:
                # Get oldest pending job
                pending_jobs = self.db.list_pending_jobs()

                if pending_jobs:
                    job = pending_jobs[0]
                    await self._process_job(job["id"])
                else:
                    # No pending jobs, sleep before checking again
                    await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Worker loop error: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def _process_job(self, job_id: str):
        """
        Process single job with progress updates at each stage

        Args:
            job_id: UUID of job to process
        """
        self.current_job_id = job_id

        try:
            # Get job details
            job = self.db.read_job(job_id)
            if not job:
                logger.error(f"Job {job_id} not found in database")
                return

            video_id = job.get("video_id")
            if not video_id:
                logger.error(f"Job {job_id} has no video_id")
                await self._update_progress(job_id, "failed", 0, "Missing video_id")
                return

            # Construct YouTube URL
            video_url = f"https://youtube.com/watch?v={video_id}"

            logger.info(f"Processing job {job_id}: {video_url}")

            # Stage 0: Mark as processing
            await self._update_progress(job_id, "processing", 0)

            # Stage 1: Starting (10%)
            await self._update_progress(job_id, "processing", 10)
            await asyncio.sleep(1)

            # Stage 2: Extract metadata (30%)
            await self._update_progress(job_id, "processing", 30)

            # Stage 3: Extract audio (40%)
            await self._update_progress(job_id, "processing", 40)

            # Stage 4: Transcribe - long running (50-90%)
            await self._update_progress(job_id, "processing", 50)

            # Call transcription pipeline (blocking, run in thread pool)
            logger.info(f"Starting transcription for job {job_id}")
            result = await asyncio.to_thread(
                self.extractor.process_video,
                video_url
            )

            # Update progress during simulated transcription stages
            for progress in [60, 70, 80, 90]:
                if self.running:  # Check if still running
                    await self._update_progress(job_id, "processing", progress)
                    await asyncio.sleep(0.5)

            # Check transcription result
            if result and result.status == "success":
                logger.info(f"Job {job_id} transcription successful")

                # Update output paths with generated files
                self.db.update_output_paths(
                    job_id,
                    transcript_md=result.transcript_path,
                    transcript_json=result.transcript_path.replace(".md", ".json")
                    if result.transcript_path
                    else None,
                    metadata=f"{result.output_dir}/metadata.json"
                    if result.output_dir
                    else None,
                )

                # Mark completed
                await self._update_progress(job_id, "completed", 100)

            else:
                # Transcription failed
                error_msg = result.error_message if result else "Unknown error"
                logger.error(f"Job {job_id} transcription failed: {error_msg}")
                self.db.update_job_status(
                    job_id, status="failed", error_message=error_msg
                )
                await self._broadcast_update(job_id)

        except Exception as e:
            logger.error(f"Job {job_id} failed with exception: {e}", exc_info=True)
            self.db.update_job_status(
                job_id, status="failed", error_message=str(e)
            )
            await self._broadcast_update(job_id)

        finally:
            self.current_job_id = None

    async def _update_progress(
        self, job_id: str, status: str, progress: float, error_message: Optional[str] = None
    ):
        """
        Update job progress in database and broadcast via WebSocket

        Args:
            job_id: Job UUID
            status: Job status (pending/processing/completed/failed)
            progress: Progress percentage (0-100)
            error_message: Optional error message if failed
        """
        if error_message:
            self.db.update_job_status(
                job_id, status=status, error_message=error_message
            )
        else:
            self.db.update_job_status(job_id, status=status, progress=progress)

        await self._broadcast_update(job_id)

    async def _broadcast_update(self, job_id: str):
        """
        Broadcast job update to all WebSocket clients

        Args:
            job_id: Job UUID to broadcast
        """
        job = self.db.read_job(job_id)
        if job:
            await self.ws_manager.broadcast(
                {
                    "type": "job_update",
                    "job": job,
                }
            )
