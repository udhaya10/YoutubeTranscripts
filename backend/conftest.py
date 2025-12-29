"""
Pytest configuration and fixtures for backend tests
"""
import pytest
import tempfile
import os
from pathlib import Path
import sqlite3


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_db():
    """Create temporary SQLite database for tests"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def metadata_dir(temp_dir):
    """Create temporary metadata directory structure"""
    metadata_dir = Path(temp_dir) / "metadata"
    (metadata_dir / "channels").mkdir(parents=True)
    (metadata_dir / "playlists").mkdir(parents=True)
    (metadata_dir / "videos").mkdir(parents=True)
    return metadata_dir


@pytest.fixture
def sample_video_data():
    """Sample video metadata for testing"""
    return {
        "video_id": "dQw4w9WgXcQ",
        "title": "Rick Astley - Never Gonna Give You Up",
        "duration": 212,
        "upload_date": "20091025",
        "channel": "Rick Astley",
        "views": 1726832413,
    }


@pytest.fixture
def sample_playlist_data():
    """Sample playlist metadata for testing"""
    return {
        "playlist_id": "PLxxxxx",
        "title": "Uploads",
        "video_count": 42,
        "videos": [
            {"video_id": "vid1", "title": "Video 1", "duration": 180},
            {"video_id": "vid2", "title": "Video 2", "duration": 210},
        ]
    }


@pytest.fixture
def sample_channel_data():
    """Sample channel metadata for testing"""
    return {
        "channel_id": "UCuAXFkgsw1L7xaCfnd5JJOw",
        "channel_name": "Rick Astley",
        "playlists": [
            {"playlist_id": "pl1", "title": "Uploads", "video_count": 42},
            {"playlist_id": "pl2", "title": "Favorites", "video_count": 18},
        ]
    }
