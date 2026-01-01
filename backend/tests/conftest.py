"""
Shared test fixtures and configuration for all test files
Provides reusable test data, fixtures, and pytest configuration
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock


# ============================================================================
# YOUTUBE TEST DATA FIXTURES - Shared across test files
# ============================================================================

# Rick Astley - Never Gonna Give You Up (stable, well-known video)
RICK_ASTLEY_VIDEO = {
    "id": "dQw4w9WgXcQ",
    "title": "Never Gonna Give You Up",
    "uploader": "Rick Astley",
    "uploader_id": "RickAstleyVEVO",
    "duration": 213,
    "description": "The official music video for the song",
    "view_count": 1000000000,
    "upload_date": "20091025",
    "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
}

# YouTube Music Playlist
YOUTUBE_PLAYLIST = {
    "id": "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",
    "title": "Greatest Hits",
    "uploader": "Rick Astley",
    "description": "Best songs compilation",
    "video_count": 5,
    "entries": [
        {
            "id": "vid1",
            "title": "Song 1 - Greatest Hit",
            "uploader": "Rick Astley",
            "duration": 200,
        },
        {
            "id": "vid2",
            "title": "Song 2 - Classic",
            "uploader": "Rick Astley",
            "duration": 250,
        },
        {
            "id": "vid3",
            "title": "Song 3 - Favorite",
            "uploader": "Rick Astley",
            "duration": 180,
        },
        {
            "id": "vid4",
            "title": "Song 4 - Best",
            "uploader": "Rick Astley",
            "duration": 220,
        },
        {
            "id": "vid5",
            "title": "Song 5 - Iconic",
            "uploader": "Rick Astley",
            "duration": 210,
        },
    ],
}

# Google Developers Channel
GOOGLE_DEVS_CHANNEL = {
    "id": "UC_x5XG1OV2P6uZZ5FSM9Ttw",
    "title": "Google Developers",
    "description": "The official Google Developers channel",
    "subscriber_count": 5000000,
    "video_count": 1000,
    "playlist_count": 10,
    "entries": [
        {
            "_type": "playlist",
            "id": "PL_playlist1",
            "title": "Android Development",
            "playlist_count": 50,
        },
        {
            "_type": "playlist",
            "id": "PL_playlist2",
            "title": "Web Development",
            "playlist_count": 75,
        },
        {
            "_type": "playlist",
            "id": "PL_playlist3",
            "title": "Cloud Platform",
            "playlist_count": 100,
        },
    ],
}


# ============================================================================
# PYTEST FIXTURES
# ============================================================================


@pytest.fixture
def youtube_test_data():
    """Provides complete YouTube test data dictionary"""
    return {
        "video": RICK_ASTLEY_VIDEO.copy(),
        "playlist": YOUTUBE_PLAYLIST.copy(),
        "channel": GOOGLE_DEVS_CHANNEL.copy(),
    }


@pytest.fixture
def video_data():
    """Provides Rick Astley video test data"""
    return RICK_ASTLEY_VIDEO.copy()


@pytest.fixture
def playlist_data():
    """Provides YouTube playlist test data"""
    return YOUTUBE_PLAYLIST.copy()


@pytest.fixture
def channel_data():
    """Provides YouTube channel test data"""
    return GOOGLE_DEVS_CHANNEL.copy()


@pytest.fixture
def mock_youtube_extractor(monkeypatch):
    """Provides mock YouTube extractor with pre-configured responses"""
    mock_extractor = MagicMock()

    # Default mock returns
    mock_extractor.extract_video.return_value = RICK_ASTLEY_VIDEO.copy()
    mock_extractor.extract_playlist.return_value = YOUTUBE_PLAYLIST.copy()
    mock_extractor.extract_channel.return_value = GOOGLE_DEVS_CHANNEL.copy()

    return mock_extractor


@pytest.fixture
def temp_dir(tmp_path):
    """Provides temporary directory path for test files"""
    return str(tmp_path)


@pytest.fixture
def temp_json_path(tmp_path):
    """Provides temporary JSON file path for testing"""
    return str(tmp_path / "test_data.json")


@pytest.fixture
def temp_md_path(tmp_path):
    """Provides temporary Markdown file path for testing"""
    return str(tmp_path / "test_data.md")


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )
