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
            await asyncio.sleep(10)
            return MockProcessingResult(status="success")

        mock_extractor.process_video = AsyncMock(side_effect=slow_transcribe)

        await worker.start()
        await asyncio.sleep(0.5)  # Let it start processing

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
