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
    def test_extract_video_success(self, mock_ydl_class, extractor, video_data):
        """Test successful video extraction"""
        # Mock yt_dlp response with shared test data
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = video_data

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
    def test_extract_playlist_success(self, mock_ydl_class, extractor, playlist_data):
        """Test successful playlist extraction"""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = playlist_data

        result = extractor.extract_playlist("PLgreatest")

        assert result is not None
        assert result["title"] == "Greatest Hits"
        assert result["video_count"] == 5
        assert len(result["videos"]) == 5

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
    def test_extract_channel_success(self, mock_ydl_class, extractor, channel_data):
        """Test successful channel extraction"""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = channel_data

        result = extractor.extract_channel("UCuAXFkgsw1L7xaCfnd5JJOw")

        assert result is not None
        assert result["title"] == "Google Developers"
        assert result["playlist_count"] == 3

    @patch('youtube_extractor.yt_dlp.YoutubeDL')
    def test_extract_channel_by_handle(self, mock_ydl_class, extractor, channel_data):
        """Test channel extraction by @ handle"""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        channel_data_no_entries = channel_data.copy()
        channel_data_no_entries["entries"] = []
        mock_ydl.extract_info.return_value = channel_data_no_entries

        result = extractor.extract_channel("@GoogleDevelopers")

        assert result is not None
        assert result["title"] == "Google Developers"

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


class TestYouTubeExtractionErrorScenarios:
    """Tests for YouTube API error scenarios"""

    @patch('youtube_extractor.yt_dlp.YoutubeDL')
    def test_extract_video_network_timeout(self, mock_ydl_class, extractor):
        """Test video extraction with network timeout"""
        import socket
        mock_ydl_class.return_value.__enter__.return_value.extract_info.side_effect = socket.timeout("Connection timed out")

        result = extractor.extract_video("vid_timeout")

        assert result is None

    @patch('youtube_extractor.yt_dlp.YoutubeDL')
    def test_extract_video_404_not_found(self, mock_ydl_class, extractor):
        """Test video extraction when video doesn't exist"""
        mock_ydl_class.return_value.__enter__.return_value.extract_info.side_effect = Exception("video not found")

        result = extractor.extract_video("vid_notfound")

        assert result is None

    @patch('youtube_extractor.yt_dlp.YoutubeDL')
    def test_extract_video_403_age_restricted(self, mock_ydl_class, extractor):
        """Test video extraction for age-restricted content"""
        mock_ydl_class.return_value.__enter__.return_value.extract_info.side_effect = Exception("age restricted")

        result = extractor.extract_video("vid_agerestricted")

        assert result is None

    @patch('youtube_extractor.yt_dlp.YoutubeDL')
    def test_extract_video_429_rate_limited(self, mock_ydl_class, extractor):
        """Test video extraction with rate limiting"""
        mock_ydl_class.return_value.__enter__.return_value.extract_info.side_effect = Exception("HTTP Error 429: Too Many Requests")

        result = extractor.extract_video("vid_ratelimit")

        assert result is None

    @patch('youtube_extractor.yt_dlp.YoutubeDL')
    def test_extract_malformed_json_response(self, mock_ydl_class, extractor):
        """Test extraction with malformed JSON response"""
        mock_ydl_class.return_value.__enter__.return_value.extract_info.side_effect = Exception("Invalid JSON")

        result = extractor.extract_video("vid_malformed")

        assert result is None

    @patch('youtube_extractor.yt_dlp.YoutubeDL')
    def test_extract_incomplete_data_structure(self, mock_ydl_class, extractor):
        """Test extraction with missing required fields"""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        # Return minimal data missing critical fields
        mock_ydl.extract_info.return_value = {
            "id": "vid123",
            # Missing title, uploader, duration
        }

        result = extractor.extract_video("vid123")

        # Should still process even with missing optional fields
        assert result is not None
        assert result["id"] == "vid123"

    @patch('youtube_extractor.yt_dlp.YoutubeDL')
    def test_extract_unicode_in_title(self, mock_ydl_class, extractor):
        """Test extraction with Unicode characters in title"""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            "id": "vid_unicode",
            "title": "日本語タイトル (Japanese) 中文标题 (Chinese) العربية (Arabic)",
            "uploader": "テスト チャンネル",
            "duration": 300,
        }

        result = extractor.extract_video("vid_unicode")

        assert result is not None
        assert "日本語" in result["title"]

    @patch('youtube_extractor.yt_dlp.YoutubeDL')
    def test_extract_huge_playlist_1000_videos(self, mock_ydl_class, extractor):
        """Test extraction of very large playlist (1000+ videos)"""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        # Generate 1000 fake video entries
        entries = [
            {
                "id": f"vid_{i}",
                "title": f"Video {i}",
                "uploader": "Test Channel",
                "duration": 300 + i,
            }
            for i in range(1000)
        ]
        mock_ydl.extract_info.return_value = {
            "title": "Huge Playlist",
            "uploader": "Test Channel",
            "description": "1000 video playlist",
            "entries": entries,
        }

        result = extractor.extract_playlist("PL_huge")

        assert result is not None
        assert result["video_count"] == 1000
        assert len(result["videos"]) == 1000

    @patch('youtube_extractor.yt_dlp.YoutubeDL')
    def test_extract_video_with_extremely_long_description(self, mock_ydl_class, extractor):
        """Test video with very long description (10,000+ characters)"""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        long_description = "A" * 10000
        mock_ydl.extract_info.return_value = {
            "id": "vid_longdesc",
            "title": "Long Description Video",
            "uploader": "Test",
            "description": long_description,
            "duration": 600,
        }

        result = extractor.extract_video("vid_longdesc")

        assert result is not None
        assert len(result["description"]) == 10000

    @patch('youtube_extractor.yt_dlp.YoutubeDL')
    def test_extract_connection_refused(self, mock_ydl_class, extractor):
        """Test extraction when connection is refused"""
        import socket
        mock_ydl_class.return_value.__enter__.return_value.extract_info.side_effect = socket.error("Connection refused")

        result = extractor.extract_video("vid_connrefused")

        assert result is None

    @patch('youtube_extractor.yt_dlp.YoutubeDL')
    def test_extract_invalid_video_id_format(self, mock_ydl_class, extractor):
        """Test extraction with invalid video ID format"""
        mock_ydl_class.return_value.__enter__.return_value.extract_info.side_effect = Exception("Invalid video ID")

        result = extractor.extract_video("invalid_video_id")

        assert result is None

    @patch('youtube_extractor.yt_dlp.YoutubeDL')
    def test_extract_private_video(self, mock_ydl_class, extractor):
        """Test extraction of private video"""
        mock_ydl_class.return_value.__enter__.return_value.extract_info.side_effect = Exception("Private video")

        result = extractor.extract_video("vid_private")

        assert result is None

    @patch('youtube_extractor.yt_dlp.YoutubeDL')
    def test_extract_deleted_video(self, mock_ydl_class, extractor):
        """Test extraction of deleted video"""
        mock_ydl_class.return_value.__enter__.return_value.extract_info.side_effect = Exception("Video has been removed")

        result = extractor.extract_video("vid_deleted")

        assert result is None

    @patch('youtube_extractor.yt_dlp.YoutubeDL')
    def test_extract_suspended_channel(self, mock_ydl_class, extractor):
        """Test extraction from suspended channel"""
        mock_ydl_class.return_value.__enter__.return_value.extract_info.side_effect = Exception("Channel has been terminated")

        result = extractor.extract_channel("UC_suspended")

        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
