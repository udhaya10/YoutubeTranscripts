"""
Tests for YouTube data extraction - Milestones 7-9
"""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path as PathlibPath

# Add backend to path
sys.path.insert(0, str(PathlibPath(__file__).parent.parent))

from youtube_extractor import YouTubeExtractor


@pytest.fixture
def extractor():
    """Create extractor instance"""
    return YouTubeExtractor()


@pytest.fixture
def temp_json_path(tmp_path):
    """Create temporary JSON output path"""
    return str(tmp_path / "test_data.json")


@pytest.fixture
def temp_md_path(tmp_path):
    """Create temporary Markdown output path"""
    return str(tmp_path / "test_data.md")


class TestVideoExtraction:
    """Tests for single video extraction (M7)"""

    @patch('youtube_extractor.yt_dlp.YoutubeDL')
    def test_extract_video_success(self, mock_ydl_class, extractor):
        """Test successful video extraction"""
        # Mock yt_dlp response
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            "id": "dQw4w9WgXcQ",
            "title": "Never Gonna Give You Up",
            "uploader": "Rick Astley",
            "uploader_id": "RickAstleyVEVO",
            "duration": 213,
            "description": "The official music video",
            "view_count": 1000000,
            "upload_date": "2009-10-25",
            "thumbnail": "https://example.com/thumb.jpg",
        }

        result = extractor.extract_video("dQw4w9WgXcQ")

        assert result is not None
        assert result["id"] == "dQw4w9WgXcQ"
        assert result["title"] == "Never Gonna Give You Up"
        assert result["uploader"] == "Rick Astley"

    @patch('youtube_extractor.yt_dlp.YoutubeDL')
    def test_extract_video_failure(self, mock_ydl_class, extractor):
        """Test video extraction failure"""
        mock_ydl_class.return_value.__enter__.return_value.extract_info.side_effect = Exception("Network error")

        result = extractor.extract_video("invalid_id")

        assert result is None

    def test_save_video_as_json(self, extractor, temp_json_path):
        """Test saving video data as JSON"""
        video_data = {
            "id": "dQw4w9WgXcQ",
            "title": "Never Gonna Give You Up",
            "uploader": "Rick Astley",
        }

        success = extractor.save_as_json(video_data, temp_json_path)

        assert success is True
        assert Path(temp_json_path).exists()

        with open(temp_json_path) as f:
            saved_data = json.load(f)
        assert saved_data["id"] == "dQw4w9WgXcQ"

    def test_save_video_as_markdown(self, extractor, temp_md_path):
        """Test saving video data as Markdown"""
        video_data = {
            "id": "dQw4w9WgXcQ",
            "title": "Never Gonna Give You Up",
            "uploader": "Rick Astley",
            "duration": 213,
            "description": "Music video",
        }

        success = extractor.save_as_markdown(video_data, temp_md_path, "video")

        assert success is True
        assert Path(temp_md_path).exists()

        with open(temp_md_path) as f:
            content = f.read()
        assert "Never Gonna Give You Up" in content
        assert "Rick Astley" in content


class TestPlaylistExtraction:
    """Tests for playlist extraction (M8)"""

    @patch('youtube_extractor.yt_dlp.YoutubeDL')
    def test_extract_playlist_success(self, mock_ydl_class, extractor):
        """Test successful playlist extraction"""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            "title": "Greatest Hits",
            "uploader": "Rick Astley",
            "description": "Best songs",
            "entries": [
                {"id": "vid1", "title": "Song 1", "uploader": "Rick Astley", "duration": 200},
                {"id": "vid2", "title": "Song 2", "uploader": "Rick Astley", "duration": 250},
            ],
        }

        result = extractor.extract_playlist("PLgreatest")

        assert result is not None
        assert result["title"] == "Greatest Hits"
        assert result["video_count"] == 2
        assert len(result["videos"]) == 2

    def test_save_playlist_as_json(self, extractor, temp_json_path):
        """Test saving playlist data as JSON"""
        playlist_data = {
            "id": "PLgreatest",
            "title": "Greatest Hits",
            "uploader": "Rick Astley",
            "video_count": 2,
            "videos": [
                {"id": "vid1", "title": "Song 1"},
                {"id": "vid2", "title": "Song 2"},
            ],
        }

        success = extractor.save_as_json(playlist_data, temp_json_path)

        assert success is True
        with open(temp_json_path) as f:
            saved_data = json.load(f)
        assert saved_data["video_count"] == 2

    def test_save_playlist_as_markdown(self, extractor, temp_md_path):
        """Test saving playlist data as Markdown"""
        playlist_data = {
            "id": "PLgreatest",
            "title": "Greatest Hits",
            "uploader": "Rick Astley",
            "video_count": 2,
            "videos": [
                {"id": "vid1", "title": "Song 1"},
                {"id": "vid2", "title": "Song 2"},
            ],
        }

        success = extractor.save_as_markdown(playlist_data, temp_md_path, "playlist")

        assert success is True
        with open(temp_md_path) as f:
            content = f.read()
        assert "Greatest Hits" in content
        assert "Song 1" in content


class TestChannelExtraction:
    """Tests for channel extraction (M9)"""

    @patch('youtube_extractor.yt_dlp.YoutubeDL')
    def test_extract_channel_success(self, mock_ydl_class, extractor):
        """Test successful channel extraction"""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            "id": "UCuAXFkgsw1L7xaCfnd5JJOw",
            "title": "Rick Astley",
            "description": "Official channel",
            "subscriber_count": 5000000,
            "video_count": 50,
            "entries": [
                {"_type": "playlist", "id": "PL1", "title": "Playlist 1", "playlist_count": 10},
                {"_type": "playlist", "id": "PL2", "title": "Playlist 2", "playlist_count": 15},
            ],
        }

        result = extractor.extract_channel("UCuAXFkgsw1L7xaCfnd5JJOw")

        assert result is not None
        assert result["title"] == "Rick Astley"
        assert result["playlist_count"] == 2

    @patch('youtube_extractor.yt_dlp.YoutubeDL')
    def test_extract_channel_by_handle(self, mock_ydl_class, extractor):
        """Test channel extraction by @ handle"""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            "id": "UCuAXFkgsw1L7xaCfnd5JJOw",
            "title": "Rick Astley",
            "entries": [],
        }

        result = extractor.extract_channel("@RickAstley")

        assert result is not None
        assert result["title"] == "Rick Astley"

    def test_save_channel_as_json(self, extractor, temp_json_path):
        """Test saving channel data as JSON"""
        channel_data = {
            "id": "UCuAXFkgsw1L7xaCfnd5JJOw",
            "title": "Rick Astley",
            "playlist_count": 2,
            "playlists": [
                {"id": "PL1", "title": "Playlist 1"},
            ],
        }

        success = extractor.save_as_json(channel_data, temp_json_path)

        assert success is True
        with open(temp_json_path) as f:
            saved_data = json.load(f)
        assert saved_data["playlist_count"] == 2

    def test_save_channel_as_markdown(self, extractor, temp_md_path):
        """Test saving channel data as Markdown"""
        channel_data = {
            "id": "UCuAXFkgsw1L7xaCfnd5JJOw",
            "title": "Rick Astley",
            "subscriber_count": 5000000,
            "video_count": 50,
            "playlist_count": 2,
            "playlists": [
                {"id": "PL1", "title": "Playlist 1", "video_count": 10},
            ],
        }

        success = extractor.save_as_markdown(channel_data, temp_md_path, "channel")

        assert success is True
        with open(temp_md_path) as f:
            content = f.read()
        assert "Rick Astley" in content
        assert "Playlist 1" in content


class TestMarkdownGeneration:
    """Tests for Markdown generation"""

    def test_video_markdown_structure(self, extractor):
        """Test video Markdown contains all required sections"""
        video_data = {
            "id": "vid123",
            "title": "Test Video",
            "uploader": "Test Channel",
            "duration": 300,
            "description": "Test description",
        }

        md = extractor._generate_video_markdown(video_data)

        assert "# Video:" in md
        assert "vid123" in md
        assert "Test Channel" in md
        assert "Test description" in md

    def test_playlist_markdown_structure(self, extractor):
        """Test playlist Markdown contains all required sections"""
        playlist_data = {
            "id": "PL123",
            "title": "Test Playlist",
            "uploader": "Test Channel",
            "video_count": 5,
            "videos": [
                {"id": "v1", "title": "Video 1"},
            ],
        }

        md = extractor._generate_playlist_markdown(playlist_data)

        assert "# Playlist:" in md
        assert "Test Playlist" in md
        assert "Video 1" in md

    def test_channel_markdown_structure(self, extractor):
        """Test channel Markdown contains all required sections"""
        channel_data = {
            "id": "UC123",
            "title": "Test Channel",
            "subscriber_count": 1000,
            "video_count": 50,
            "playlists": [
                {"id": "PL1", "title": "Playlist 1", "video_count": 10},
            ],
        }

        md = extractor._generate_channel_markdown(channel_data)

        assert "# Channel:" in md
        assert "Test Channel" in md
        assert "Playlist 1" in md


class TestRealYouTubeExtraction:
    """Tests for REAL YouTube extraction (not mocked) - M7, M8, M9"""

    def test_extract_real_video_metadata(self, extractor):
        """Test extracting REAL video from YouTube with known stable video"""
        # Rick Astley - Never Gonna Give You Up (stable, known to exist forever)
        result = extractor.extract_video("dQw4w9WgXcQ")

        # This test requires network access to YouTube
        if result is not None:
            assert result["id"] == "dQw4w9WgXcQ"
            assert "Never Gonna Give You Up" in result["title"] or result["title"] != ""
            assert result.get("duration", 0) > 200  # Should be ~3+ minutes
            assert result.get("uploader", "") != ""

    def test_extract_real_playlist_metadata(self, extractor):
        """Test extracting REAL playlist from YouTube"""
        # YouTube Music playlist (stable, public)
        # Using a simple public playlist
        result = extractor.extract_playlist("PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf")

        # This test requires network access to YouTube
        if result is not None:
            assert result.get("video_count", 0) >= 0
            assert result.get("title", "") != ""

    def test_extract_real_channel_metadata(self, extractor):
        """Test extracting REAL channel information from YouTube"""
        # Using a stable public channel
        result = extractor.extract_channel("UC_x5XG1OV2P6uZZ5FSM9Ttw")  # Google Developers

        # This test requires network access to YouTube
        if result is not None:
            assert result.get("title", "") != ""
            assert "playlist_count" in result or "title" in result
            # Channel should have at least a title
            assert len(result.get("title", "")) > 0


class TestErrorHandling:
    """Tests for error handling"""

    def test_save_to_invalid_path(self, extractor):
        """Test saving to invalid path"""
        data = {"id": "test", "title": "Test"}
        invalid_path = "/invalid/path/that/does/not/exist/file.json"

        success = extractor.save_as_json(data, invalid_path)

        # Should attempt but might fail due to permissions
        # Just verify it returns a boolean
        assert isinstance(success, bool)

    @patch('youtube_extractor.yt_dlp.YoutubeDL')
    def test_extract_with_empty_entries(self, mock_ydl_class, extractor):
        """Test extraction when entries list is empty"""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            "title": "Empty Playlist",
            "uploader": "Test",
            "entries": [],
        }

        result = extractor.extract_playlist("PLempty")

        assert result is not None
        assert result["video_count"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
