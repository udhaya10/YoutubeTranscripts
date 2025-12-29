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


class TestRequestModels:
    """Tests for request/response models"""

    def test_extract_request(self):
        """Test ExtractRequest model"""
        req = ExtractRequest(url="https://youtu.be/test123")
        assert req.url == "https://youtu.be/test123"

    def test_extract_response(self):
        """Test ExtractResponse model"""
        resp = ExtractResponse(
            type="video",
            id="test123",
            title="Test",
            metadata={}
        )
        assert resp.type == "video"
        assert resp.id == "test123"

    def test_job_request_minimal(self):
        """Test JobRequest with required fields"""
        req = JobRequest(video_id="vid123")
        assert req.video_id == "vid123"
        assert req.video_title is None

    def test_job_request_full(self):
        """Test JobRequest with all fields"""
        req = JobRequest(
            video_id="vid123",
            video_title="Test",
            playlist_id="pl123"
        )
        assert req.video_id == "vid123"
        assert req.video_title == "Test"
        assert req.playlist_id == "pl123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
