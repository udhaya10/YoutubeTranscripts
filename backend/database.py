"""
SQLite database module for job queue management
"""
import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class JobDatabase:
    """Manages SQLite database for video transcription job queue"""

    def __init__(self, db_path: str = "/app/queue/queue.db"):
        """Initialize database connection

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema if not exists"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    video_id TEXT NOT NULL,
                    video_title TEXT,
                    playlist_id TEXT,
                    channel_id TEXT,
                    status TEXT DEFAULT 'pending',
                    progress FLOAT DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    output_paths TEXT,
                    metadata TEXT
                )
            """)
            conn.commit()
            logger.info(f"Database initialized: {self.db_path}")

    def create_job(
        self,
        job_id: str,
        video_id: str,
        video_title: Optional[str] = None,
        playlist_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new job in the queue

        Args:
            job_id: Unique job identifier
            video_id: YouTube video ID
            video_title: Video title (optional)
            playlist_id: Playlist ID if part of playlist (optional)
            channel_id: Channel ID (optional)
            metadata: Additional metadata as dict (optional)

        Returns:
            Created job dict
        """
        metadata_json = json.dumps(metadata) if metadata else None

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("""
                INSERT INTO jobs (
                    id, video_id, video_title, playlist_id,
                    channel_id, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (job_id, video_id, video_title, playlist_id, channel_id, metadata_json))
            conn.commit()

        logger.info(f"Created job: {job_id}")
        return self.read_job(job_id)

    def read_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Read a job by ID

        Args:
            job_id: Job ID to read

        Returns:
            Job dict or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_dict(row)

    def update_job_status(
        self,
        job_id: str,
        status: str,
        progress: float = 0.0,
        error_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update job status

        Args:
            job_id: Job ID to update
            status: New status (pending, processing, completed, failed)
            progress: Progress percentage (0-100)
            error_message: Error message if failed (optional)

        Returns:
            Updated job dict
        """
        with sqlite3.connect(self.db_path) as conn:
            if status == "processing" and progress > 0:
                conn.execute("""
                    UPDATE jobs
                    SET status = ?, progress = ?, started_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, progress, job_id))
            elif status == "completed":
                conn.execute("""
                    UPDATE jobs
                    SET status = ?, progress = 100.0, completed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, job_id))
            elif status == "failed":
                conn.execute("""
                    UPDATE jobs
                    SET status = ?, error_message = ?, retry_count = retry_count + 1
                    WHERE id = ?
                """, (status, error_message, job_id))
            else:
                conn.execute("""
                    UPDATE jobs
                    SET status = ?, progress = ?
                    WHERE id = ?
                """, (status, progress, job_id))
            conn.commit()

        logger.info(f"Updated job {job_id}: status={status}, progress={progress}%")
        return self.read_job(job_id)

    def list_jobs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List jobs, optionally filtered by status

        Args:
            status: Filter by status (optional)

        Returns:
            List of job dicts
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if status:
                cursor = conn.execute("SELECT * FROM jobs WHERE status = ?", (status,))
            else:
                cursor = conn.execute("SELECT * FROM jobs")
            rows = cursor.fetchall()

        return [self._row_to_dict(row) for row in rows]

    def list_pending_jobs(self) -> List[Dict[str, Any]]:
        """Get all pending jobs

        Returns:
            List of pending job dicts
        """
        return self.list_jobs(status="pending")

    def update_output_paths(
        self,
        job_id: str,
        transcript_md: Optional[str] = None,
        transcript_json: Optional[str] = None,
        metadata_file: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update output file paths for a completed job

        Args:
            job_id: Job ID
            transcript_md: Path to markdown transcript
            transcript_json: Path to JSON transcript
            metadata_file: Path to metadata file

        Returns:
            Updated job dict
        """
        output_paths = {
            "transcript_md": transcript_md,
            "transcript_json": transcript_json,
            "metadata": metadata_file,
        }
        output_paths_json = json.dumps(output_paths)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE jobs
                SET output_paths = ?
                WHERE id = ?
            """, (output_paths_json, job_id))
            conn.commit()

        return self.read_job(job_id)

    def recover_orphaned_jobs(self, max_retries: int = 3) -> List[str]:
        """Recover jobs stuck in 'processing' state from crashed worker

        Called on startup to handle jobs left in processing state if the
        worker crashed. Resets them to pending if retry count < max_retries.

        Args:
            max_retries: Maximum number of retries before marking permanently failed

        Returns:
            List of job IDs that were recovered
        """
        recovered_jobs = []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Find jobs stuck in processing state
            cursor = conn.execute("""
                SELECT id, retry_count FROM jobs
                WHERE status = 'processing'
            """)
            orphaned = cursor.fetchall()

            for job_row in orphaned:
                job_id = job_row["id"]
                retry_count = job_row["retry_count"] or 0

                if retry_count >= max_retries:
                    # Too many retries, mark as permanently failed
                    conn.execute("""
                        UPDATE jobs
                        SET status = 'failed',
                            error_message = 'Max retries exceeded after worker crash'
                        WHERE id = ?
                    """, (job_id,))
                    logger.warning(
                        f"Job {job_id} marked as permanently failed "
                        f"(exceeded max retries: {retry_count}/{max_retries})"
                    )
                else:
                    # Reset to pending for retry
                    conn.execute("""
                        UPDATE jobs
                        SET status = 'pending', progress = 0.0, error_message = NULL
                        WHERE id = ?
                    """, (job_id,))
                    recovered_jobs.append(job_id)
                    logger.info(
                        f"Recovered orphaned job {job_id} "
                        f"(retry {retry_count + 1}/{max_retries})"
                    )

            conn.commit()

        if recovered_jobs:
            logger.info(f"✓ Recovered {len(recovered_jobs)} orphaned jobs from crash")

        return recovered_jobs

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
        """Convert sqlite3.Row to dict with parsed JSON fields

        Args:
            row: sqlite3.Row object

        Returns:
            Dictionary with parsed JSON fields
        """
        job_dict = dict(row)

        # Parse JSON fields
        if job_dict.get("output_paths"):
            try:
                job_dict["output_paths"] = json.loads(job_dict["output_paths"])
            except (json.JSONDecodeError, TypeError):
                job_dict["output_paths"] = None

        if job_dict.get("metadata"):
            try:
                job_dict["metadata"] = json.loads(job_dict["metadata"])
            except (json.JSONDecodeError, TypeError):
                job_dict["metadata"] = None

        return job_dict
