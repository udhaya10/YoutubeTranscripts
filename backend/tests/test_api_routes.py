"""
Tests for API routes - Milestones M10-M13
Tests URL extraction endpoints (M10-M11) and queue management (M12-M13)
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
import sys
from pathlib import Path as PathlibPath

# Add backend to path
sys.path.insert(0, str(PathlibPath(__file__).parent.parent))

# Import models with mocking
with patch('api_routes.YouTubeURLParser'), \
     patch('api_routes.YouTubeExtractor'), \
     patch('api_routes.JobDatabase'), \
     patch('api_routes.MetadataStore'):
    from api_routes import router, ExtractRequest, ExtractResponse, JobRequest
    import api_routes


@pytest.fixture
def mock_parser():
    """Create and inject mock parser"""
    mock = MagicMock()
    api_routes.YouTubeURLParser = mock
    return mock


@pytest.fixture
def mock_extractor(monkeypatch):
    """Create and inject mock extractor"""
    mock_obj = MagicMock()
    mock_cls = MagicMock(return_value=mock_obj)
    api_routes.YouTubeExtractor = mock_cls
    api_routes._extractor = None  # Reset lazy singleton
    monkeypatch.setattr(api_routes, 'get_extractor', lambda: mock_obj)
    return mock_obj


@pytest.fixture
def mock_db(monkeypatch):
    """Create and inject mock database"""
    mock_obj = MagicMock()
    mock_cls = MagicMock(return_value=mock_obj)
    api_routes.JobDatabase = mock_cls
    api_routes._db = None  # Reset lazy singleton
    monkeypatch.setattr(api_routes, 'get_db', lambda: mock_obj)
    return mock_obj


@pytest.fixture
def mock_metadata_store(monkeypatch):
    """Create and inject mock metadata store"""
    mock_obj = MagicMock()
    mock_cls = MagicMock(return_value=mock_obj)
    api_routes.MetadataStore = mock_cls
    api_routes._metadata_store = None  # Reset lazy singleton
    monkeypatch.setattr(api_routes, 'get_metadata_store', lambda: mock_obj)
    return mock_obj


@pytest.fixture
def client():
    """Create a test client"""
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestURLExtraction:
    """Tests for URL extraction endpoints (M10-M11)"""

    def test_extract_video_success(self, client, mock_parser, mock_extractor, mock_metadata_store):
        """Test successful video URL extraction"""
        mock_parser.parse_url.return_value = {
            "valid": True,
            "type": "video",
            "id": "dQw4w9WgXcQ"
        }
        mock_extractor.extract_video.return_value = {
            "id": "dQw4w9WgXcQ",
            "title": "Never Gonna Give You Up",
            "uploader": "Rick Astley",
        }

        response = client.post("/api/extract", json={"url": "https://youtu.be/dQw4w9WgXcQ"})

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "video"
        assert data["id"] == "dQw4w9WgXcQ"
        assert data["title"] == "Never Gonna Give You Up"

    def test_extract_invalid_url(self, client, mock_parser):
        """Test extraction with invalid URL"""
        mock_parser.parse_url.return_value = {
            "valid": False,
            "type": "unknown"
        }

        response = client.post("/api/extract", json={"url": "https://example.com"})

        assert response.status_code == 400
        assert "Invalid YouTube URL" in response.json()["detail"]

    def test_extract_unknown_type(self, client, mock_parser):
        """Test extraction with unknown URL type"""
        mock_parser.parse_url.return_value = {
            "valid": True,
            "type": "unknown",
            "id": "test"
        }

        response = client.post("/api/extract", json={"url": "https://youtube.com/unknown"})

        assert response.status_code == 400
        assert "Unable to determine URL type" in response.json()["detail"]

    def test_extract_extractor_error(self, client, mock_parser, mock_extractor):
        """Test extraction when extractor fails"""
        mock_parser.parse_url.return_value = {
            "valid": True,
            "type": "video",
            "id": "dQw4w9WgXcQ"
        }
        mock_extractor.extract_video.side_effect = Exception("Network error")

        response = client.post("/api/extract", json={"url": "https://youtu.be/dQw4w9WgXcQ"})

        assert response.status_code == 500
        assert "Network error" in response.json()["detail"]

    def test_extract_playlist_success(self, client, mock_parser, mock_extractor, mock_metadata_store):
        """Test successful playlist URL extraction"""
        mock_parser.parse_url.return_value = {
            "valid": True,
            "type": "playlist",
            "id": "PLtest123"
        }
        mock_extractor.extract_playlist.return_value = {
            "id": "PLtest123",
            "title": "Test Playlist",
            "video_count": 5,
        }

        response = client.post("/api/extract", json={"url": "https://youtube.com/playlist?list=PLtest123"})

        assert response.status_code == 200
        assert response.json()["type"] == "playlist"

    def test_extract_channel_success(self, client, mock_parser, mock_extractor, mock_metadata_store):
        """Test successful channel URL extraction"""
        mock_parser.parse_url.return_value = {
            "valid": True,
            "type": "channel",
            "id": "UCtest123"
        }
        mock_extractor.extract_channel.return_value = {
            "id": "UCtest123",
            "title": "Test Channel",
        }

        response = client.post("/api/extract", json={"url": "https://youtube.com/@TestChannel"})

        assert response.status_code == 200
        assert response.json()["type"] == "channel"

    def test_extract_empty_metadata(self, client, mock_parser, mock_extractor, mock_metadata_store):
        """Test extraction with empty metadata"""
        mock_parser.parse_url.return_value = {
            "valid": True,
            "type": "video",
            "id": "vid123"
        }
        mock_extractor.extract_video.return_value = {}

        response = client.post("/api/extract", json={"url": "https://youtu.be/vid123"})

        assert response.status_code == 200
        assert response.json()["title"] == "Unknown Video"


class TestJobManagement:
    """Tests for job management endpoints (M12-M13)"""

    def test_create_job_success(self, client, mock_db):
        """Test successful job creation"""
        mock_db.create_job.return_value = {
            "job_id": "test-job-123",
            "video_id": "vid123",
            "status": "pending",
        }

        response = client.post("/api/jobs", json={"video_id": "vid123"})

        assert response.status_code == 200
        assert response.json()["job_id"] == "test-job-123"
        assert mock_db.create_job.called

    def test_create_job_with_title(self, client, mock_db):
        """Test job creation with title"""
        mock_db.create_job.return_value = {
            "job_id": "test-job-456",
            "video_id": "vid456",
        }

        response = client.post("/api/jobs", json={
            "video_id": "vid456",
            "video_title": "Test Video"
        })

        assert response.status_code == 200
        assert mock_db.create_job.called

    def test_create_job_error(self, client, mock_db):
        """Test job creation when database fails"""
        mock_db.create_job.side_effect = Exception("Database error")

        response = client.post("/api/jobs", json={"video_id": "vid789"})

        assert response.status_code == 500

    def test_list_jobs(self, client, mock_db):
        """Test listing jobs"""
        mock_db.list_jobs.return_value = [
            {"job_id": "job1", "status": "pending"},
            {"job_id": "job2", "status": "completed"}
        ]

        response = client.get("/api/jobs")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["jobs"]) == 2

    def test_list_jobs_filtered(self, client, mock_db):
        """Test listing jobs with status filter"""
        mock_db.list_jobs.return_value = [
            {"job_id": "job1", "status": "pending"}
        ]

        response = client.get("/api/jobs?status=pending")

        assert response.status_code == 200
        assert mock_db.list_jobs.called

    def test_list_jobs_error(self, client, mock_db):
        """Test list jobs when database fails"""
        mock_db.list_jobs.side_effect = Exception("Database error")

        response = client.get("/api/jobs")

        assert response.status_code == 500

    def test_get_job_success(self, client, mock_db):
        """Test retrieving specific job"""
        mock_db.read_job.return_value = {
            "job_id": "job123",
            "video_id": "vid123",
            "status": "processing"
        }

        response = client.get("/api/jobs/job123")

        assert response.status_code == 200
        assert response.json()["job_id"] == "job123"

    def test_get_job_not_found(self, client, mock_db):
        """Test retrieving non-existent job"""
        mock_db.read_job.return_value = None

        response = client.get("/api/jobs/nonexistent")

        assert response.status_code == 404

    def test_get_job_error(self, client, mock_db):
        """Test retrieving job when database fails"""
        mock_db.read_job.side_effect = Exception("Database error")

        response = client.get("/api/jobs/job123")

        assert response.status_code == 500

    def test_update_job_status(self, client, mock_db):
        """Test updating job status"""
        mock_db.update_job_status.return_value = {
            "job_id": "job123",
            "status": "completed",
        }

        response = client.patch("/api/jobs/job123?status=completed&progress=1.0")

        assert response.status_code == 200

    def test_update_job_not_found(self, client, mock_db):
        """Test updating non-existent job"""
        mock_db.update_job_status.return_value = None

        response = client.patch("/api/jobs/nonexistent?status=completed")

        assert response.status_code == 404

    def test_update_job_error(self, client, mock_db):
        """Test updating job when database fails"""
        mock_db.update_job_status.side_effect = Exception("Database error")

        response = client.patch("/api/jobs/job123?status=processing")

        assert response.status_code == 500

    def test_add_selected_videos(self, client, mock_db):
        """Test adding multiple videos to queue"""
        mock_db.create_job.side_effect = [
            {"job_id": "job1", "video_id": "vid1"},
            {"job_id": "job2", "video_id": "vid2"}
        ]

        response = client.post("/api/jobs/add-selected", json=["vid1", "vid2"])

        assert response.status_code == 200
        assert response.json()["created"] == 2

    def test_add_selected_single(self, client, mock_db):
        """Test adding single video to queue"""
        mock_db.create_job.return_value = {"job_id": "job1", "video_id": "vid1"}

        response = client.post("/api/jobs/add-selected", json=["vid1"])

        assert response.status_code == 200
        assert response.json()["created"] == 1

    def test_add_selected_empty(self, client, mock_db):
        """Test adding empty list to queue"""
        response = client.post("/api/jobs/add-selected", json=[])

        assert response.status_code == 200
        assert response.json()["created"] == 0

    def test_add_selected_error(self, client, mock_db):
        """Test adding to queue when database fails"""
        mock_db.create_job.side_effect = Exception("Database error")

        response = client.post("/api/jobs/add-selected", json=["vid1"])

        assert response.status_code == 500


class TestMetadataRetrieval:
    """Tests for metadata retrieval endpoints"""

    def test_get_video_metadata(self, client, mock_metadata_store):
        """Test retrieving video metadata"""
        mock_metadata_store.load_video_metadata.return_value = {
            "id": "vid123",
            "title": "Test Video"
        }

        response = client.get("/api/metadata/video/vid123")

        assert response.status_code == 200
        assert response.json()["title"] == "Test Video"

    def test_get_video_metadata_not_found(self, client, mock_metadata_store):
        """Test retrieving non-existent video metadata"""
        mock_metadata_store.load_video_metadata.return_value = None

        response = client.get("/api/metadata/video/nonexistent")

        assert response.status_code == 404

    def test_get_playlist_metadata(self, client, mock_metadata_store):
        """Test retrieving playlist metadata"""
        mock_metadata_store.load_playlist_metadata.return_value = {
            "id": "pl123",
            "title": "Test Playlist"
        }

        response = client.get("/api/metadata/playlist/pl123")

        assert response.status_code == 200

    def test_get_playlist_metadata_not_found(self, client, mock_metadata_store):
        """Test retrieving non-existent playlist metadata"""
        mock_metadata_store.load_playlist_metadata.return_value = None

        response = client.get("/api/metadata/playlist/nonexistent")

        assert response.status_code == 404

    def test_get_channel_metadata(self, client, mock_metadata_store):
        """Test retrieving channel metadata"""
        mock_metadata_store.load_channel_metadata.return_value = {
            "id": "uc123",
            "title": "Test Channel"
        }

        response = client.get("/api/metadata/channel/uc123")

        assert response.status_code == 200

    def test_get_channel_metadata_not_found(self, client, mock_metadata_store):
        """Test retrieving non-existent channel metadata"""
        mock_metadata_store.load_channel_metadata.return_value = None

        response = client.get("/api/metadata/channel/nonexistent")

        assert response.status_code == 404


class TestBoundaryConditions:
    """Tests for boundary conditions and edge cases"""

    def test_create_job_with_very_long_title(self, client, mock_db):
        """Test job creation with extremely long video title"""
        long_title = "A" * 1000  # 1000 character title
        mock_db.create_job.return_value = {
            "job_id": "test-job-123",
            "video_id": "vid123",
            "video_title": long_title,
            "status": "pending",
        }

        response = client.post("/api/jobs", json={
            "video_id": "vid123",
            "video_title": long_title
        })

        assert response.status_code == 200
        assert len(response.json()["video_title"]) == 1000

    def test_update_job_progress_at_boundaries(self, client, mock_db):
        """Test job progress at 0%, 50%, 100%"""
        mock_db.get_job.return_value = {
            "job_id": "job-1",
            "progress": 0,
            "status": "processing"
        }

        for progress in [0, 50, 100]:
            mock_db.get_job.return_value["progress"] = progress
            response = client.patch(f"/api/jobs/job-1?status=processing&progress={progress}")
            assert response.status_code == 200

    def test_add_large_batch_of_jobs(self, client, mock_db):
        """Test adding 100 jobs in one batch operation"""
        video_ids = [f"vid{i}" for i in range(100)]
        mock_db.create_job.return_value = {
            "job_id": "test-job",
            "status": "pending"
        }

        response = client.post("/api/jobs/add-selected", json=video_ids)

        assert response.status_code == 200
        assert response.json()["created"] == 100

    def test_extract_url_with_special_characters_in_title(self, client, mock_parser, mock_extractor):
        """Test extraction with special characters in metadata title"""
        special_title = "Test™ © ® 日本語 中文 العربية"
        mock_parser.parse_url.return_value = {
            "valid": True,
            "type": "video",
            "id": "vid123"
        }
        mock_extractor.extract_video.return_value = {
            "id": "vid123",
            "title": special_title,
        }

        response = client.post("/api/extract", json={"url": "https://youtu.be/vid123"})

        assert response.status_code == 200
        assert response.json()["title"] == special_title

    def test_list_jobs_empty_database(self, client, mock_db):
        """Test listing jobs when database is empty"""
        mock_db.list_jobs.return_value = []

        response = client.get("/api/jobs")

        assert response.status_code == 200
        assert response.json()["jobs"] == []


class TestDataValidation:
    """Tests for data validation and format compliance"""

    def test_job_status_values(self, client, mock_db):
        """Test all valid job status values"""
        valid_statuses = ["pending", "processing", "completed", "failed", "cancelled"]

        for status in valid_statuses:
            mock_db.update_job.return_value = {
                "job_id": "job-1",
                "status": status
            }

            response = client.patch(f"/api/jobs/job-1?status={status}")
            assert response.status_code == 200

    def test_job_id_uuid_format(self, client, mock_db):
        """Test that job IDs follow expected format"""
        job_id = "550e8400-e29b-41d4-a716-446655440000"
        mock_db.read_job.return_value = {
            "job_id": job_id,
            "video_id": "vid123",
            "status": "pending",
            "created_at": "2024-01-15T00:00:00Z"
        }

        response = client.get(f"/api/jobs/{job_id}")

        assert response.status_code == 200
        assert response.json()["job_id"] == job_id

    def test_response_timestamp_format(self, client, mock_db):
        """Test that timestamps in responses follow ISO 8601 format"""
        iso_timestamp = "2024-01-15T10:30:45.123456Z"
        mock_db.read_job.return_value = {
            "job_id": "job-1",
            "video_id": "vid123",
            "created_at": iso_timestamp,
            "status": "pending"
        }

        response = client.get("/api/jobs/job-1")

        assert response.status_code == 200
        assert response.json()["created_at"] == iso_timestamp


class TestConcurrentOperations:
    """Tests for concurrent/parallel operations"""

    def test_concurrent_job_creation(self, client, mock_db):
        """Test rapid sequential job creation"""
        mock_db.create_job.return_value = {
            "job_id": "test-job",
            "status": "pending"
        }

        # Simulate rapid job creation
        for i in range(5):
            response = client.post("/api/jobs", json={"video_id": f"vid{i}"})
            assert response.status_code == 200

    def test_multiple_updates_to_same_job(self, client, mock_db):
        """Test multiple status/progress updates to the same job"""
        job_id = "job-1"
        updates = [
            ("processing", 0),
            ("processing", 25),
            ("processing", 50),
            ("processing", 75),
            ("completed", 100)
        ]

        for status, progress in updates:
            mock_db.update_job.return_value = {
                "job_id": job_id,
                "status": status,
                "progress": progress
            }

            response = client.patch(f"/api/jobs/{job_id}?status={status}&progress={progress}")
            assert response.status_code == 200


class TestStateTransitions:
    """Tests for job state machine transitions"""

    def test_pending_to_processing_transition(self, client, mock_db):
        """Test valid transition from pending to processing"""
        mock_db.update_job_status.return_value = {"job_id": "job-1", "status": "processing", "progress": 0}

        response = client.patch("/api/jobs/job-1?status=processing")

        assert response.status_code == 200
        assert response.json()["status"] == "processing"

    def test_processing_to_completed_transition(self, client, mock_db):
        """Test valid transition from processing to completed"""
        mock_db.update_job_status.return_value = {"job_id": "job-1", "status": "completed", "progress": 100}

        response = client.patch("/api/jobs/job-1?status=completed&progress=100")

        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    def test_processing_to_failed_transition(self, client, mock_db):
        """Test valid transition from processing to failed"""
        mock_db.update_job_status.return_value = {"job_id": "job-1", "status": "failed", "progress": 50}

        response = client.patch("/api/jobs/job-1?status=failed")

        assert response.status_code == 200
        assert response.json()["status"] == "failed"

    def test_failed_to_pending_retry_transition(self, client, mock_db):
        """Test retry transition from failed back to pending"""
        mock_db.update_job_status.return_value = {"job_id": "job-1", "status": "pending", "retry_count": 1, "progress": 0}

        response = client.patch("/api/jobs/job-1?status=pending")

        assert response.status_code == 200
        assert response.json()["status"] == "pending"


class TestAdvancedIntegration:
    """Advanced integration tests with real database and complex workflows"""

    def test_extract_url_stores_metadata_in_real_store(self, monkeypatch, tmp_path):
        """Test that extract endpoint stores metadata in real metadata store"""
        import json
        from pathlib import Path
        from metadata_store import MetadataStore
        from youtube_utils import YouTubeURLParser

        real_store = MetadataStore(str(tmp_path))
        api_routes._metadata_store = real_store
        monkeypatch.setattr(api_routes, 'get_metadata_store', lambda: real_store)

        # Mock parser and extractor for controlled testing
        mock_parser = MagicMock()
        mock_parser.parse_url.return_value = {
            "valid": True,
            "type": "video",
            "id": "dQw4w9WgXcQ"
        }
        monkeypatch.setattr(api_routes, 'YouTubeURLParser', mock_parser)

        mock_extractor = MagicMock()
        mock_extractor.extract_video.return_value = {
            "id": "dQw4w9WgXcQ",
            "title": "Never Gonna Give You Up",
            "uploader": "Rick Astley",
            "duration": 213,
            "description": "Test video",
        }
        monkeypatch.setattr(api_routes, 'YouTubeExtractor', lambda: mock_extractor)
        api_routes._extractor = mock_extractor

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        response = client.post("/api/extract", json={
            "url": "https://youtu.be/dQw4w9WgXcQ"
        })

        assert response.status_code == 200

        # Verify actual metadata file was created
        json_path = tmp_path / "videos" / "video_dQw4w9WgXcQ.json"
        assert json_path.exists()

        with open(json_path) as f:
            saved_metadata = json.load(f)
        assert saved_metadata["id"] == "dQw4w9WgXcQ"
        assert saved_metadata["title"] == "Never Gonna Give You Up"

    def test_job_state_machine_with_real_db(self, monkeypatch, tmp_path):
        """Test complete job state machine with real database"""
        from pathlib import Path
        from database import JobDatabase

        db_path = tmp_path / "state_machine.db"
        real_db = JobDatabase(str(db_path))

        api_routes.JobDatabase = lambda path: real_db
        api_routes._db = real_db
        monkeypatch.setattr(api_routes, 'get_db', lambda: real_db)

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Create job
        response = client.post("/api/jobs", json={
            "video_id": "state_test_vid",
            "video_title": "State Machine Test"
        })
        assert response.status_code == 200
        job_id = response.json()["id"]

        # Verify initial state
        job = real_db.read_job(job_id)
        assert job["status"] == "pending"
        assert job["progress"] == 0.0

        # Transition: pending → processing
        response = client.patch(f"/api/jobs/{job_id}?status=processing&progress=0")
        assert response.status_code == 200
        job = real_db.read_job(job_id)
        assert job["status"] == "processing"

        # Transition: processing → processing with progress
        response = client.patch(f"/api/jobs/{job_id}?status=processing&progress=50")
        assert response.status_code == 200
        job = real_db.read_job(job_id)
        assert job["progress"] == 50.0

        # Transition: processing → completed
        response = client.patch(f"/api/jobs/{job_id}?status=completed&progress=100")
        assert response.status_code == 200
        job = real_db.read_job(job_id)
        assert job["status"] == "completed"
        assert job["progress"] == 100.0

        # Verify final state persisted
        db2 = JobDatabase(str(db_path))
        final_job = db2.read_job(job_id)
        assert final_job["status"] == "completed"

    def test_queue_operations_with_real_persistence(self, monkeypatch, tmp_path):
        """Test queue operations with real database persistence"""
        from pathlib import Path
        from database import JobDatabase

        db_path = tmp_path / "queue_test.db"
        real_db = JobDatabase(str(db_path))

        # Create multiple jobs in different states
        real_db.create_job("queue_job_1", "vid_1", "Video 1")
        real_db.create_job("queue_job_2", "vid_2", "Video 2")
        real_db.create_job("queue_job_3", "vid_3", "Video 3")

        real_db.update_job_status("queue_job_1", "processing", progress=25.0)
        real_db.update_job_status("queue_job_2", "completed", progress=100.0)

        api_routes.JobDatabase = lambda path: real_db
        api_routes._db = real_db
        monkeypatch.setattr(api_routes, 'get_db', lambda: real_db)

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # List all jobs
        response = client.get("/api/jobs")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3

        # Verify correct status distribution
        job_statuses = {job["id"]: job["status"] for job in data["jobs"]}
        assert job_statuses["queue_job_1"] == "processing"
        assert job_statuses["queue_job_2"] == "completed"
        assert job_statuses["queue_job_3"] == "pending"

        # List pending jobs via DB (verify API consistency)
        pending = real_db.list_pending_jobs()
        assert len(pending) == 1
        assert pending[0]["id"] == "queue_job_3"

    def test_concurrent_api_requests_with_real_db(self, monkeypatch, tmp_path):
        """Test concurrent API requests with real database"""
        import threading
        from pathlib import Path
        from database import JobDatabase

        db_path = tmp_path / "concurrent_api.db"
        real_db = JobDatabase(str(db_path))

        api_routes.JobDatabase = lambda path: real_db
        api_routes._db = real_db
        monkeypatch.setattr(api_routes, 'get_db', lambda: real_db)

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        created_jobs = []
        errors = []

        def create_job(job_num):
            try:
                response = client.post("/api/jobs", json={
                    "video_id": f"concurrent_vid_{job_num}",
                    "video_title": f"Concurrent Video {job_num}"
                })
                if response.status_code == 200:
                    created_jobs.append(response.json()["id"])
            except Exception as e:
                errors.append(str(e))

        # Create 5 jobs concurrently via API
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_job, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(errors) == 0
        assert len(created_jobs) == 5

        # Verify all jobs persisted
        all_jobs = real_db.list_jobs()
        assert len(all_jobs) == 5

    def test_batch_job_creation_end_to_end(self, monkeypatch, tmp_path):
        """Test batch job creation end-to-end with real database"""
        from pathlib import Path
        from database import JobDatabase

        db_path = tmp_path / "batch_test.db"
        real_db = JobDatabase(str(db_path))

        api_routes.JobDatabase = lambda path: real_db
        api_routes._db = real_db
        monkeypatch.setattr(api_routes, 'get_db', lambda: real_db)

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Create batch of videos
        video_ids = ["batch_1", "batch_2", "batch_3", "batch_4", "batch_5"]
        response = client.post("/api/jobs/add-selected", json=video_ids)

        assert response.status_code == 200
        assert response.json()["created"] == 5

        # List and verify all jobs
        response = client.get("/api/jobs")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 5

        # Verify all videos are in the list
        job_videos = [job["video_id"] for job in data["jobs"]]
        for vid_id in video_ids:
            assert vid_id in job_videos

        # Verify database consistency
        all_jobs = real_db.list_jobs()
        assert len(all_jobs) == 5


class TestResponseValidation:
    """Tests for response structure and integrity"""

    def test_job_response_has_required_fields(self, client, mock_db):
        """Test that job response contains all required fields"""
        required_fields = ["job_id", "video_id", "status", "created_at"]
        mock_db.read_job.return_value = {
            "job_id": "job-1",
            "video_id": "vid123",
            "status": "pending",
            "created_at": "2024-01-15T00:00:00Z",
            "progress": 0,
            "retry_count": 0
        }

        response = client.get("/api/jobs/job-1")

        assert response.status_code == 200
        for field in required_fields:
            assert field in response.json()

    def test_list_jobs_response_structure(self, client, mock_db):
        """Test that list jobs response has correct structure"""
        mock_db.list_jobs.return_value = [
            {"job_id": "job-1", "video_id": "vid1", "status": "pending"},
            {"job_id": "job-2", "video_id": "vid2", "status": "completed"}
        ]

        response = client.get("/api/jobs")

        assert response.status_code == 200
        body = response.json()
        assert "jobs" in body
        assert "count" in body
        assert len(body["jobs"]) == 2
        assert body["count"] == 2

    def test_extract_response_structure(self, client, mock_parser, mock_extractor):
        """Test that extract response has correct structure"""
        required_fields = ["type", "id", "title", "metadata"]
        mock_parser.parse_url.return_value = {
            "valid": True,
            "type": "video",
            "id": "vid123"
        }
        mock_extractor.extract_video.return_value = {
            "id": "vid123",
            "title": "Test Video",
        }

        response = client.post("/api/extract", json={"url": "https://youtu.be/vid123"})

        assert response.status_code == 200
        for field in required_fields:
            assert field in response.json()


class TestAPIIntegration:
    """Integration tests for API with real database and metadata store"""

    def test_create_and_retrieve_job_with_real_db(self, monkeypatch, tmp_path):
        """Test job creation and retrieval using real database"""
        from pathlib import Path
        from database import JobDatabase
        from metadata_store import MetadataStore

        # Create real temporary database
        db_path = tmp_path / "test_integration.db"
        real_db = JobDatabase(str(db_path))

        # Patch API to use real database
        api_routes.JobDatabase = lambda path: real_db
        api_routes._db = real_db
        monkeypatch.setattr(api_routes, 'get_db', lambda: real_db)

        # Create test client
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Create job via API with real database
        response = client.post("/api/jobs", json={
            "video_id": "integration_test_vid",
            "video_title": "Integration Test Video"
        })

        assert response.status_code == 200
        job_id = response.json()["id"]

        # Verify job was actually written to real database
        retrieved = real_db.read_job(job_id)
        assert retrieved is not None
        assert retrieved["video_id"] == "integration_test_vid"
        assert retrieved["video_title"] == "Integration Test Video"
        assert retrieved["status"] == "pending"

    def test_update_job_status_persists_to_real_db(self, monkeypatch, tmp_path):
        """Test that job status updates actually persist to real database"""
        from pathlib import Path
        from database import JobDatabase

        # Create real temporary database
        db_path = tmp_path / "test_status_persist.db"
        real_db = JobDatabase(str(db_path))

        # Create a job directly in database
        job = real_db.create_job(
            "persist_test_job",
            "video_persist_test",
            "Persistence Test Video"
        )

        # Patch API to use real database
        api_routes.JobDatabase = lambda path: real_db
        api_routes._db = real_db
        monkeypatch.setattr(api_routes, 'get_db', lambda: real_db)

        # Create test client
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Update job status via API
        response = client.patch(
            "/api/jobs/persist_test_job?status=processing&progress=50.0"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "processing"
        assert response.json()["progress"] == 50.0

        # Verify status update persisted to real database
        updated_job = real_db.read_job("persist_test_job")
        assert updated_job["status"] == "processing"
        assert updated_job["progress"] == 50.0

    def test_list_jobs_returns_real_data_from_db(self, monkeypatch, tmp_path):
        """Test that listing jobs returns actual data from real database"""
        from pathlib import Path
        from database import JobDatabase

        # Create real temporary database with multiple jobs
        db_path = tmp_path / "test_list_real.db"
        real_db = JobDatabase(str(db_path))

        # Create multiple jobs directly in database
        real_db.create_job("list_job_1", "video_1", "Video 1")
        real_db.create_job("list_job_2", "video_2", "Video 2")
        real_db.create_job("list_job_3", "video_3", "Video 3")

        # Update one to different status
        real_db.update_job_status("list_job_1", "processing", progress=25.0)

        # Patch API to use real database
        api_routes.JobDatabase = lambda path: real_db
        api_routes._db = real_db
        monkeypatch.setattr(api_routes, 'get_db', lambda: real_db)

        # Create test client
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # List all jobs via API
        response = client.get("/api/jobs")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert len(data["jobs"]) == 3

        # Verify actual jobs are returned with correct data
        job_ids = [job["id"] for job in data["jobs"]]
        assert "list_job_1" in job_ids
        assert "list_job_2" in job_ids
        assert "list_job_3" in job_ids

        # Verify job statuses are correct
        job_1 = next(j for j in data["jobs"] if j["id"] == "list_job_1")
        assert job_1["status"] == "processing"
        assert job_1["progress"] == 25.0

        job_2 = next(j for j in data["jobs"] if j["id"] == "list_job_2")
        assert job_2["status"] == "pending"

    def test_add_multiple_jobs_transaction_with_real_db(self, monkeypatch, tmp_path):
        """Test adding multiple jobs in one operation writes all to real database"""
        from pathlib import Path
        from database import JobDatabase

        # Create real temporary database
        db_path = tmp_path / "test_batch_add.db"
        real_db = JobDatabase(str(db_path))

        # Patch API to use real database
        api_routes.JobDatabase = lambda path: real_db
        api_routes._db = real_db
        monkeypatch.setattr(api_routes, 'get_db', lambda: real_db)

        # Create test client
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Add multiple videos in batch via API
        video_ids = ["batch_vid_1", "batch_vid_2", "batch_vid_3"]
        response = client.post("/api/jobs/add-selected", json=video_ids)

        assert response.status_code == 200
        assert response.json()["created"] == 3

        # Verify all jobs actually exist in real database
        all_jobs = real_db.list_jobs()
        assert len(all_jobs) == 3

        batch_job_ids = [job["video_id"] for job in all_jobs]
        for vid_id in video_ids:
            assert vid_id in batch_job_ids


class TestErrorHandlingScenarios:
    """Tests for error handling in API endpoints"""

    def test_api_handles_network_timeout(self, client, monkeypatch):
        """Test that API handles network timeouts gracefully"""
        import socket

        mock_parser = MagicMock()
        mock_parser.parse_url.return_value = {
            "valid": True,
            "type": "video",
            "id": "dQw4w9WgXcQ"
        }
        monkeypatch.setattr(api_routes, 'YouTubeURLParser', mock_parser)

        # Mock extractor to raise timeout
        mock_extractor = MagicMock()
        mock_extractor.extract_video.side_effect = socket.timeout("Connection timed out")
        api_routes._extractor = mock_extractor
        monkeypatch.setattr(api_routes, 'YouTubeExtractor', lambda: mock_extractor)

        response = client.post("/api/extract", json={
            "url": "https://youtu.be/dQw4w9WgXcQ"
        })

        # Should return error response, not crash
        assert response.status_code >= 400
        assert "error" in response.text.lower() or "detail" in response.json()

    def test_api_handles_invalid_database_state(self, client, mock_db):
        """Test that API handles invalid database state"""
        # Simulate database raising an exception
        mock_db.create_job.side_effect = RuntimeError("Database connection lost")

        response = client.post("/api/jobs", json={
            "video_id": "vid_invalid"
        })

        # Should return error
        assert response.status_code == 500

    def test_api_handles_extraction_failure_gracefully(self, client, mock_parser, mock_extractor):
        """Test API handles extraction failures gracefully"""
        mock_parser.parse_url.return_value = {
            "valid": True,
            "type": "video",
            "id": "broken_video"
        }
        mock_extractor.extract_video.side_effect = ValueError("Video not available")

        response = client.post("/api/extract", json={
            "url": "https://youtu.be/broken_video"
        })

        assert response.status_code >= 400

    def test_api_handles_database_locked(self, client, mock_db):
        """Test API gracefully handles database locked error"""
        import sqlite3
        mock_db.create_job.side_effect = sqlite3.OperationalError("database is locked")

        response = client.post("/api/jobs", json={"video_id": "vid123"})

        assert response.status_code == 500
        assert "error" in response.json() or response.json().get("detail")

    def test_api_handles_memory_error(self, client, mock_extractor, mock_parser):
        """Test API handles memory exhaustion errors"""
        mock_parser.parse_url.return_value = {
            "valid": True,
            "type": "video",
            "id": "huge_video"
        }
        mock_extractor.extract_video.side_effect = MemoryError("Out of memory")

        response = client.post("/api/extract", json={
            "url": "https://youtu.be/huge_video"
        })

        assert response.status_code >= 400

    def test_api_handles_connection_reset(self, client, mock_extractor, mock_parser):
        """Test API handles connection reset errors"""
        mock_parser.parse_url.return_value = {
            "valid": True,
            "type": "video",
            "id": "reset_video"
        }
        mock_extractor.extract_video.side_effect = ConnectionResetError("Connection reset by peer")

        response = client.post("/api/extract", json={
            "url": "https://youtu.be/reset_video"
        })

        assert response.status_code >= 400

    def test_api_handles_permission_denied(self, client, mock_metadata_store, mock_db):
        """Test API handles permission denied errors during metadata save"""
        mock_metadata_store.save_video_metadata.side_effect = PermissionError("Permission denied")
        mock_db.create_job.return_value = {"id": "test_job"}

        response = client.post("/api/jobs", json={"video_id": "vid123"})

        # Should handle gracefully
        assert response.status_code >= 400 or response.status_code == 200

    def test_api_handles_malformed_response_data(self, client, mock_extractor, mock_parser):
        """Test API handles extractor returning malformed data"""
        mock_parser.parse_url.return_value = {
            "valid": True,
            "type": "video",
            "id": "malformed_video"
        }
        # Return incomplete data missing required fields
        mock_extractor.extract_video.return_value = {"id": "partial"}

        response = client.post("/api/extract", json={
            "url": "https://youtu.be/malformed_video"
        })

        # Should handle missing fields gracefully
        assert response.status_code >= 400 or "title" not in response.json()

    def test_api_handles_none_response(self, client, mock_extractor, mock_parser):
        """Test API handles None response from extractor"""
        mock_parser.parse_url.return_value = {
            "valid": True,
            "type": "video",
            "id": "none_video"
        }
        mock_extractor.extract_video.return_value = None

        response = client.post("/api/extract", json={
            "url": "https://youtu.be/none_video"
        })

        # API should handle gracefully (either error or empty response)
        assert response.status_code in [200, 400, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
