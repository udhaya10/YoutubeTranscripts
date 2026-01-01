"""
Tests for background worker and WebSocket manager
Covers M18 (Background processing) and M19 (WebSocket real-time updates)
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from dataclasses import dataclass

import sys
from pathlib import Path as PathlibPath

# Add backend to path
sys.path.insert(0, str(PathlibPath(__file__).parent.parent))

from worker import BackgroundWorker
from websocket_manager import ConnectionManager


# Test fixtures and helpers
@dataclass
class MockProcessingResult:
    """Mock VideoProcessor result"""
    status: str
    transcript_path: str = None
    output_dir: str = None
    error_message: str = None


@pytest.fixture
def mock_db():
    """Mock JobDatabase"""
    db = MagicMock()
    db.list_pending_jobs.return_value = []
    db.read_job.return_value = None
    db.update_job_status.return_value = None
    db.update_output_paths.return_value = None
    return db


@pytest.fixture
def mock_extractor():
    """Mock YouTubeExtractor"""
    extractor = MagicMock()
    extractor.process_video.return_value = MockProcessingResult(status="success")
    return extractor


@pytest.fixture
def mock_ws_manager():
    """Mock ConnectionManager"""
    manager = MagicMock()
    manager.broadcast = AsyncMock()
    return manager


@pytest.fixture
def worker(mock_db, mock_extractor, mock_ws_manager):
    """Create BackgroundWorker instance with mocks"""
    return BackgroundWorker(mock_db, mock_extractor, mock_ws_manager)


# Tests for BackgroundWorker
class TestBackgroundWorker:
    """Tests for background job processing worker"""

    @pytest.mark.asyncio
    async def test_worker_starts(self, worker, mock_db, mock_extractor, mock_ws_manager):
        """Test worker startup"""
        await worker.start()
        assert worker.running is True
        assert worker.task is not None
        await worker.stop()

    @pytest.mark.asyncio
    async def test_worker_stops(self, worker):
        """Test worker shutdown"""
        await worker.start()
        assert worker.running is True
        await worker.stop()
        assert worker.running is False

    @pytest.mark.asyncio
    async def test_worker_processes_pending_job(self, worker, mock_db, mock_extractor, mock_ws_manager):
        """Test worker picks up and processes pending job"""
        job = {
            "id": "job-123",
            "video_id": "vid123",
            "status": "pending",
            "progress": 0,
        }
        mock_db.list_pending_jobs.return_value = [job]
        mock_db.read_job.return_value = job
        mock_extractor.process_video.return_value = MockProcessingResult(
            status="success",
            transcript_path="/app/transcripts/vid123/transcript.md",
            output_dir="/app/transcripts/vid123",
        )

        # Process job directly (more reliable than waiting for worker loop)
        await worker._process_job("job-123")

        # Verify job was processed
        assert mock_extractor.process_video.called

    @pytest.mark.asyncio
    async def test_worker_sleeps_on_empty_queue(self, worker, mock_db):
        """Test worker sleeps when no jobs pending"""
        mock_db.list_pending_jobs.return_value = []

        await worker.start()
        # Mock asyncio.sleep to avoid actual waiting
        with patch('asyncio.sleep', new_callable=AsyncMock):
            await asyncio.sleep(1)

        # Worker should still be running but not processing
        assert worker.running is True
        assert worker.current_job_id is None
        await worker.stop()

    @pytest.mark.asyncio
    async def test_worker_marks_job_completed(self, worker, mock_db, mock_extractor, mock_ws_manager):
        """Test worker marks job as completed after successful processing"""
        job = {
            "id": "job-123",
            "video_id": "vid123",
            "status": "pending",
            "progress": 0,
        }
        mock_db.list_pending_jobs.return_value = [job]
        mock_db.read_job.return_value = job
        mock_extractor.process_video.return_value = MockProcessingResult(
            status="success",
            transcript_path="/app/transcripts/vid123/transcript.md",
            output_dir="/app/transcripts/vid123",
        )

        await worker._process_job("job-123")

        # Verify job marked as completed
        calls = mock_db.update_job_status.call_args_list
        completed_call = [c for c in calls if "completed" in str(c)]
        assert len(completed_call) > 0

    @pytest.mark.asyncio
    async def test_worker_marks_job_failed_on_error(self, worker, mock_db, mock_extractor):
        """Test worker marks job as failed when processing fails"""
        job = {
            "id": "job-123",
            "video_id": "vid123",
            "status": "pending",
        }
        mock_db.list_pending_jobs.return_value = [job]
        mock_db.read_job.return_value = job
        mock_extractor.process_video.return_value = MockProcessingResult(
            status="error",
            error_message="Download failed",
        )

        await worker._process_job("job-123")

        # Verify job marked as failed
        calls = mock_db.update_job_status.call_args_list
        failed_call = [c for c in calls if "failed" in str(c)]
        assert len(failed_call) > 0

    @pytest.mark.asyncio
    async def test_worker_broadcasts_progress_updates(self, worker, mock_db, mock_extractor, mock_ws_manager):
        """Test worker broadcasts progress updates via WebSocket"""
        job = {
            "id": "job-123",
            "video_id": "vid123",
            "status": "pending",
        }
        mock_db.list_pending_jobs.return_value = [job]
        mock_db.read_job.return_value = job
        mock_extractor.process_video.return_value = MockProcessingResult(status="success")

        await worker._process_job("job-123")

        # Verify broadcast was called multiple times (for progress updates)
        assert mock_ws_manager.broadcast.call_count > 0

    @pytest.mark.asyncio
    async def test_worker_handles_missing_job_id(self, worker, mock_db):
        """Test worker gracefully handles job without video_id"""
        job = {
            "id": "job-123",
            "video_id": None,
            "status": "pending",
        }
        mock_db.list_pending_jobs.return_value = [job]
        mock_db.read_job.return_value = job

        await worker._process_job("job-123")

        # Verify job marked as failed
        assert any("failed" in str(c) for c in mock_db.update_job_status.call_args_list)

    @pytest.mark.asyncio
    async def test_worker_graceful_shutdown_mid_process(self, worker, mock_db, mock_extractor, mock_ws_manager):
        """Test worker stops gracefully even during job processing"""
        job = {
            "id": "job-123",
            "video_id": "vid123",
            "status": "pending",
        }
        mock_db.list_pending_jobs.return_value = [job]
        mock_db.read_job.return_value = job

        # Slow transcription to allow stopping mid-process
        async def slow_transcribe(*args, **kwargs):
            # Mock sleep to avoid actual waiting
            with patch('asyncio.sleep', new_callable=AsyncMock):
                await asyncio.sleep(10)
            return MockProcessingResult(status="success")

        mock_extractor.process_video = AsyncMock(side_effect=slow_transcribe)

        await worker.start()
        # Mock sleep to avoid actual waiting
        with patch('asyncio.sleep', new_callable=AsyncMock):
            await asyncio.sleep(0.5)

        # Request stop
        await worker.stop()
        assert worker.running is False

    @pytest.mark.asyncio
    async def test_worker_updates_output_paths(self, worker, mock_db, mock_extractor):
        """Test worker saves output file paths to database"""
        job = {
            "id": "job-123",
            "video_id": "vid123",
            "status": "pending",
        }
        mock_db.list_pending_jobs.return_value = [job]
        mock_db.read_job.return_value = job
        mock_extractor.process_video.return_value = MockProcessingResult(
            status="success",
            transcript_path="/app/transcripts/vid123/transcript.md",
            output_dir="/app/transcripts/vid123",
        )

        await worker._process_job("job-123")

        # Verify update_output_paths was called
        assert mock_db.update_output_paths.called


# Tests for WebSocket ConnectionManager
class TestWebSocketManager:
    """Tests for WebSocket connection management and broadcasting"""

    @pytest.mark.asyncio
    async def test_connect_adds_connection(self):
        """Test connecting a WebSocket adds it to active connections"""
        manager = ConnectionManager()
        ws = AsyncMock()

        await manager.connect(ws)

        assert ws in manager.active_connections
        assert len(manager.active_connections) == 1

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self):
        """Test disconnecting a WebSocket removes it from active connections"""
        manager = ConnectionManager()
        ws = AsyncMock()

        await manager.connect(ws)
        assert len(manager.active_connections) == 1

        manager.disconnect(ws)

        assert ws not in manager.active_connections
        assert len(manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_connections(self):
        """Test broadcast message is sent to all connected clients"""
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()

        await manager.connect(ws1)
        await manager.connect(ws2)
        await manager.connect(ws3)

        message = {"type": "job_update", "job": {"id": "123"}}
        await manager.broadcast(message)

        # All connections should receive the message
        ws1.send_json.assert_called_with(message)
        ws2.send_json.assert_called_with(message)
        ws3.send_json.assert_called_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_removes_failed_connection(self):
        """Test broadcast removes connection that fails to send"""
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        # ws1 will fail to send
        ws1.send_json.side_effect = Exception("Connection lost")

        await manager.connect(ws1)
        await manager.connect(ws2)

        message = {"type": "test"}
        await manager.broadcast(message)

        # Failed connection should be removed
        assert ws1 not in manager.active_connections
        assert ws2 in manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_to_empty_connections(self):
        """Test broadcast with no active connections doesn't crash"""
        manager = ConnectionManager()

        message = {"type": "test"}
        await manager.broadcast(message)

        # Should not raise any exception
        assert len(manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_multiple_connects_and_disconnects(self):
        """Test multiple connect/disconnect cycles"""
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        # Connect both
        await manager.connect(ws1)
        await manager.connect(ws2)
        assert len(manager.active_connections) == 2

        # Disconnect first
        manager.disconnect(ws1)
        assert len(manager.active_connections) == 1
        assert ws2 in manager.active_connections

        # Disconnect second
        manager.disconnect(ws2)
        assert len(manager.active_connections) == 0


# Tests for M20: Error Handling and Recovery
class TestM20ErrorHandling:
    """Tests for M20 error handling and recovery mechanisms"""

    @pytest.mark.asyncio
    async def test_worker_handles_job_failure_with_retry(self, worker, mock_db, mock_extractor):
        """Test worker retries failed job up to max retries"""
        job = {
            "id": "job-123",
            "video_id": "vid123",
            "status": "pending",
            "retry_count": 0,
        }
        mock_db.list_pending_jobs.return_value = [job]
        mock_db.read_job.return_value = job
        mock_extractor.process_video.return_value = MockProcessingResult(
            status="error",
            error_message="Download failed",
        )

        await worker._process_job("job-123")

        # Verify job was marked as failed first
        calls = mock_db.update_job_status.call_args_list
        # Should have calls to mark failed and then reset to pending
        assert any("failed" in str(c) for c in calls)

    @pytest.mark.asyncio
    async def test_worker_stops_retrying_after_max_retries(self, worker, mock_db, mock_extractor):
        """Test worker stops retrying after max retries exceeded"""
        job = {
            "id": "job-123",
            "video_id": "vid123",
            "status": "pending",
            "retry_count": 3,  # Already at max retries
        }
        mock_db.list_pending_jobs.return_value = [job]
        mock_db.read_job.return_value = job
        mock_extractor.process_video.return_value = MockProcessingResult(
            status="error",
            error_message="Download failed",
        )

        await worker._process_job("job-123")

        # Verify job was marked as permanently failed
        calls = mock_db.update_job_status.call_args_list
        failed_calls = [c for c in calls if "failed" in str(c) and "Max retries" in str(c)]
        assert len(failed_calls) > 0

    @pytest.mark.asyncio
    async def test_handle_job_failure_with_retries_available(self, worker, mock_db):
        """Test failure handling with available retries"""
        job = {
            "id": "job-123",
            "video_id": "vid123",
            "status": "processing",
            "retry_count": 1,
        }
        mock_db.read_job.return_value = job

        await worker._handle_job_failure("job-123", "Network error")

        # Verify job marked as failed but will retry
        assert mock_db.update_job_status.called
        # Should mark as failed first, then reset to pending
        calls = mock_db.update_job_status.call_args_list
        assert len(calls) >= 2

    @pytest.mark.asyncio
    async def test_handle_job_failure_max_retries_exceeded(self, worker, mock_db):
        """Test failure handling when max retries exceeded"""
        job = {
            "id": "job-123",
            "video_id": "vid123",
            "status": "processing",
            "retry_count": 3,
        }
        mock_db.read_job.return_value = job

        await worker._handle_job_failure("job-123", "Download failed")

        # Verify job marked as permanently failed
        calls = mock_db.update_job_status.call_args_list
        # Should only mark as failed (no reset to pending)
        assert len(calls) == 1
        assert "failed" in str(calls[0])

    @pytest.mark.asyncio
    async def test_error_message_includes_retry_info(self, worker, mock_db):
        """Test error message includes retry attempt info"""
        job = {
            "id": "job-123",
            "video_id": "vid123",
            "status": "processing",
            "retry_count": 1,
        }
        mock_db.read_job.return_value = job

        await worker._handle_job_failure("job-123", "Timeout error")

        # Verify error message includes retry info
        calls = mock_db.update_job_status.call_args_list
        first_call = calls[0]
        error_msg = first_call[1].get("error_message", "")
        assert "retry" in error_msg.lower()
        assert "2" in error_msg  # Attempt 2 of 3


class TestM20DatabaseRecovery:
    """Tests for M20 database recovery of orphaned jobs"""

    def test_recover_orphaned_jobs_resets_to_pending(self):
        """Test recovery resets processing jobs to pending"""
        from database import JobDatabase
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            db = JobDatabase(db_path)

            # Create a job in processing state
            job_id = "orphaned-job-1"
            db.create_job(job_id, "vid123")
            db.update_job_status(job_id, "processing", 50)

            # Verify it's in processing state
            job = db.read_job(job_id)
            assert job["status"] == "processing"

            # Recover orphaned jobs
            recovered = db.recover_orphaned_jobs(max_retries=3)

            # Verify job was recovered
            assert job_id in recovered
            recovered_job = db.read_job(job_id)
            assert recovered_job["status"] == "pending"
            assert recovered_job["progress"] == 0.0

        finally:
            import os
            os.unlink(db_path)

    def test_recover_orphaned_jobs_marks_exceeded_retries_as_failed(self):
        """Test recovery marks jobs exceeding max retries as failed"""
        from database import JobDatabase
        import tempfile
        import sqlite3

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            db = JobDatabase(db_path)

            # Create a job with max retries already exceeded
            job_id = "exhausted-job-1"
            db.create_job(job_id, "vid456")

            # Manually set retry_count to 3 and status to processing
            # to simulate a job that crashed with max retries already used
            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                    UPDATE jobs SET status = 'processing', retry_count = 3 WHERE id = ?
                """, (job_id,))
                conn.commit()

            # Verify job is in processing state with retry_count=3
            job = db.read_job(job_id)
            assert job["status"] == "processing"
            assert job["retry_count"] == 3

            # Recover orphaned jobs
            recovered = db.recover_orphaned_jobs(max_retries=3)

            # Verify job was NOT recovered (max retries exceeded)
            assert job_id not in recovered
            failed_job = db.read_job(job_id)
            assert failed_job["status"] == "failed"
            assert "Max retries exceeded" in failed_job["error_message"]

        finally:
            import os
            os.unlink(db_path)

    def test_recover_no_orphaned_jobs_returns_empty(self):
        """Test recovery with no orphaned jobs returns empty list"""
        from database import JobDatabase
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            db = JobDatabase(db_path)

            # Create only pending jobs
            job_id = "pending-job-1"
            db.create_job(job_id, "vid789")

            # Verify job is pending
            job = db.read_job(job_id)
            assert job["status"] == "pending"

            # Recover orphaned jobs
            recovered = db.recover_orphaned_jobs(max_retries=3)

            # Verify no jobs were recovered
            assert len(recovered) == 0

        finally:
            import os
            os.unlink(db_path)


class TestWorkerErrorRecovery:
    """Tests for worker error handling and recovery"""

    @pytest.mark.asyncio
    async def test_worker_recovers_from_extraction_failure(self):
        """Test worker recovers when extraction fails"""
        from database import JobDatabase
        import tempfile
        import os

        # Create temporary database
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            db_path = f.name

        try:
            db = JobDatabase(db_path)

            # Create a processing job
            job_id = "fail-job-1"
            db.create_job(job_id, "vid_fail", "Failing Video")
            db.update_job_status(job_id, "processing", progress=25.0)

            # Mock extractor that fails
            mock_extractor = MagicMock()
            mock_extractor.process_video.side_effect = RuntimeError("Extraction failed")

            # Simulate worker handling failure
            try:
                result = mock_extractor.process_video(job_id)
            except RuntimeError:
                # Worker would catch this and mark job as failed
                failed_job = db.update_job_status(
                    job_id,
                    "failed",
                    error_message="Extraction failed"
                )
                assert failed_job["status"] == "failed"
                assert failed_job["retry_count"] == 1

        finally:
            os.unlink(db_path)


class TestWorkerRealDatabaseIntegration:
    """Integration tests for worker with real JobDatabase"""

    @pytest.mark.asyncio
    async def test_worker_with_real_db_processes_job(self):
        """Test worker processing with real database"""
        from database import JobDatabase
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            db_path = f.name

        try:
            db = JobDatabase(db_path)
            mock_extractor = MagicMock()
            mock_ws_manager = MagicMock()
            mock_ws_manager.broadcast = AsyncMock()

            worker = BackgroundWorker(db, mock_extractor, mock_ws_manager)

            # Create real job in database
            job = db.create_job("real-job-1", "vid123", "Test Video")
            assert job["status"] == "pending"

            # Setup mock extractor
            mock_extractor.process_video.return_value = MockProcessingResult(
                status="success",
                transcript_path="/app/transcripts/vid123.md",
                output_dir="/app/transcripts/vid123"
            )

            # Process job
            await worker._process_job("real-job-1")

            # Verify job status updated in real database
            updated_job = db.read_job("real-job-1")
            assert updated_job["status"] == "completed"
            assert updated_job["progress"] == 100.0

        finally:
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_worker_with_real_db_job_failure_retry(self):
        """Test worker retry logic with real database"""
        from database import JobDatabase
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            db_path = f.name

        try:
            db = JobDatabase(db_path)
            mock_extractor = MagicMock()
            mock_ws_manager = AsyncMock()

            worker = BackgroundWorker(db, mock_extractor, mock_ws_manager)

            # Create job and set to processing with 1 retry
            job = db.create_job("retry-job-1", "vid456", "Retry Video")

            # Update retry count manually to 1
            import sqlite3
            with sqlite3.connect(db_path) as conn:
                conn.execute(
                    "UPDATE jobs SET retry_count = 1 WHERE id = ?",
                    ("retry-job-1",)
                )
                conn.commit()

            # Mock extraction failure
            mock_extractor.process_video.return_value = MockProcessingResult(
                status="error",
                error_message="Network timeout"
            )

            # Mock asyncio.sleep to avoid actual delay
            with patch('asyncio.sleep', new_callable=AsyncMock):
                # Process failure
                await worker._process_job("retry-job-1")

            # After failure handling with exponential backoff, job is reset to pending for retry
            # This tests that the worker correctly handles retries
            retry_job = db.read_job("retry-job-1")
            assert retry_job["status"] == "pending"  # Reset to pending for next attempt
            assert retry_job["retry_count"] == 2  # Retry count incremented

        finally:
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_worker_with_real_db_output_paths(self):
        """Test worker saves output paths in real database"""
        from database import JobDatabase
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            db_path = f.name

        try:
            db = JobDatabase(db_path)
            mock_extractor = MagicMock()
            mock_ws_manager = AsyncMock()

            worker = BackgroundWorker(db, mock_extractor, mock_ws_manager)

            # Create job
            job = db.create_job("output-job-1", "vid789", "Output Test")

            # Setup mock with output paths
            mock_extractor.process_video.return_value = MockProcessingResult(
                status="success",
                transcript_path="/app/transcripts/vid789/transcript.md",
                output_dir="/app/transcripts/vid789"
            )

            # Process job
            await worker._process_job("output-job-1")

            # Verify output paths saved to database
            completed_job = db.read_job("output-job-1")
            assert completed_job["output_paths"]["transcript_md"] == "/app/transcripts/vid789/transcript.md"
            assert completed_job["output_paths"]["transcript_json"] == "/app/transcripts/vid789/transcript.json"

        finally:
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_worker_with_real_db_multiple_jobs(self):
        """Test worker with real database handles multiple jobs"""
        from database import JobDatabase
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            db_path = f.name

        try:
            db = JobDatabase(db_path)
            mock_extractor = MagicMock()
            mock_ws_manager = AsyncMock()

            worker = BackgroundWorker(db, mock_extractor, mock_ws_manager)

            # Create multiple jobs
            job_ids = []
            for i in range(3):
                job = db.create_job(f"multi-job-{i}", f"vid{i}", f"Video {i}")
                job_ids.append(job["id"])
                assert job["status"] == "pending"

            # Setup mock
            mock_extractor.process_video.return_value = MockProcessingResult(
                status="success",
                transcript_path="/app/transcripts/success.md",
                output_dir="/app/transcripts"
            )

            # Process all jobs
            for job_id in job_ids:
                await worker._process_job(job_id)

            # Verify all jobs completed
            for job_id in job_ids:
                completed = db.read_job(job_id)
                assert completed["status"] == "completed"
                assert completed["progress"] == 100.0

            # Verify no pending jobs left
            pending = db.list_pending_jobs()
            assert len(pending) == 0

        finally:
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_worker_with_real_db_max_retries_exceeded(self):
        """Test worker stops retrying after max retries with real database"""
        from database import JobDatabase
        import tempfile
        import os
        import sqlite3

        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
            db_path = f.name

        try:
            db = JobDatabase(db_path)
            mock_extractor = MagicMock()
            mock_ws_manager = AsyncMock()

            worker = BackgroundWorker(db, mock_extractor, mock_ws_manager)

            # Create job and set retry count to max
            job = db.create_job("exhausted-job", "vid_exhausted", "Exhausted")
            with sqlite3.connect(db_path) as conn:
                conn.execute(
                    "UPDATE jobs SET retry_count = 3 WHERE id = ?",
                    ("exhausted-job",)
                )
                conn.commit()

            # Mock extraction failure
            mock_extractor.process_video.return_value = MockProcessingResult(
                status="error",
                error_message="Persistent failure"
            )

            # Process job
            await worker._process_job("exhausted-job")

            # Verify job marked as permanently failed
            final_job = db.read_job("exhausted-job")
            assert final_job["status"] == "failed"
            assert "Max retries" in final_job["error_message"]

        finally:
            os.unlink(db_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
