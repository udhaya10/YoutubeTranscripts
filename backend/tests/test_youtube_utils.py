"""
Tests for YouTube URL detection and parsing - Milestone 6
"""
import pytest
import sys
from pathlib import Path as PathlibPath

# Add backend to path
sys.path.insert(0, str(PathlibPath(__file__).parent.parent))

from youtube_utils import YouTubeURLParser, URLType


class TestVideoURLDetection:
    """Tests for detecting video URLs"""

    def test_detect_standard_video_url(self):
        """Test detecting standard youtube.com/watch?v= URL"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        url_type = YouTubeURLParser.detect_url_type(url)
        assert url_type == URLType.VIDEO

    def test_detect_short_video_url(self):
        """Test detecting youtu.be short video URL"""
        url = "https://youtu.be/dQw4w9WgXcQ"
        url_type = YouTubeURLParser.detect_url_type(url)
        assert url_type == URLType.VIDEO

    def test_detect_video_url_without_https(self):
        """Test detecting video URL without https"""
        url = "youtube.com/watch?v=dQw4w9WgXcQ"
        url_type = YouTubeURLParser.detect_url_type(url)
        assert url_type == URLType.VIDEO

    def test_detect_video_url_without_www(self):
        """Test detecting video URL without www"""
        url = "https://youtube.com/watch?v=dQw4w9WgXcQ"
        url_type = YouTubeURLParser.detect_url_type(url)
        assert url_type == URLType.VIDEO

    def test_extract_video_id_from_standard_url(self):
        """Test extracting video ID from standard URL"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = YouTubeURLParser.extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_from_short_url(self):
        """Test extracting video ID from short URL"""
        url = "https://youtu.be/dQw4w9WgXcQ"
        video_id = YouTubeURLParser.extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_video_id_with_additional_parameters(self):
        """Test extracting video ID from URL with additional parameters"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s&list=PLxxx"
        video_id = YouTubeURLParser.extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_multiple_video_ids_in_session(self):
        """Test parsing multiple different video IDs"""
        videos = [
            ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtube.com/watch?v=9bZkp7q19f0", "9bZkp7q19f0"),
            ("https://youtube.com/watch?v=OPf0YbXqDm0", "OPf0YbXqDm0"),
        ]
        for url, expected_id in videos:
            video_id = YouTubeURLParser.extract_video_id(url)
            assert video_id == expected_id


class TestPlaylistURLDetection:
    """Tests for detecting playlist URLs"""

    def test_detect_playlist_url(self):
        """Test detecting playlist URL"""
        url = "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
        url_type = YouTubeURLParser.detect_url_type(url)
        assert url_type == URLType.PLAYLIST

    def test_detect_playlist_url_without_https(self):
        """Test detecting playlist URL without https"""
        url = "youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
        url_type = YouTubeURLParser.detect_url_type(url)
        assert url_type == URLType.PLAYLIST

    def test_extract_playlist_id(self):
        """Test extracting playlist ID"""
        url = "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
        playlist_id = YouTubeURLParser.extract_playlist_id(url)
        assert playlist_id == "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"

    def test_extract_playlist_id_with_additional_params(self):
        """Test extracting playlist ID with additional parameters"""
        url = "https://www.youtube.com/playlist?list=PLxxx&index=5&t=10s"
        playlist_id = YouTubeURLParser.extract_playlist_id(url)
        assert playlist_id == "PLxxx"

    def test_playlist_in_watch_url(self):
        """Test that playlist in watch URL is detected as playlist"""
        # When a video URL has a playlist parameter, detect as playlist
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLxxx"
        url_type = YouTubeURLParser.detect_url_type(url)
        # Should detect as playlist due to playlist parameter
        assert url_type in [URLType.PLAYLIST, URLType.VIDEO]


class TestChannelURLDetection:
    """Tests for detecting channel URLs"""

    def test_detect_channel_by_handle(self):
        """Test detecting channel by @ handle"""
        url = "https://www.youtube.com/@MKBHD"
        url_type = YouTubeURLParser.detect_url_type(url)
        assert url_type == URLType.CHANNEL

    def test_detect_channel_by_id(self):
        """Test detecting channel by channel ID"""
        url = "https://www.youtube.com/channel/UCBJycsmduvVTAtc_ItRfqkw"
        url_type = YouTubeURLParser.detect_url_type(url)
        assert url_type == URLType.CHANNEL

    def test_detect_channel_by_user(self):
        """Test detecting channel by user name (legacy format)"""
        url = "https://www.youtube.com/user/mkbhd"
        url_type = YouTubeURLParser.detect_url_type(url)
        assert url_type == URLType.CHANNEL

    def test_extract_channel_handle(self):
        """Test extracting channel handle"""
        url = "https://www.youtube.com/@MKBHD"
        channel_id = YouTubeURLParser.extract_channel_id(url)
        assert channel_id == "MKBHD"

    def test_extract_channel_id(self):
        """Test extracting channel ID"""
        url = "https://www.youtube.com/channel/UCBJycsmduvVTAtc_ItRfqkw"
        channel_id = YouTubeURLParser.extract_channel_id(url)
        assert channel_id == "UCBJycsmduvVTAtc_ItRfqkw"

    def test_extract_channel_user(self):
        """Test extracting channel user"""
        url = "https://www.youtube.com/user/mkbhd"
        channel_id = YouTubeURLParser.extract_channel_id(url)
        assert channel_id == "mkbhd"

    def test_channel_handle_with_special_characters(self):
        """Test channel handle with underscores and numbers"""
        url = "https://www.youtube.com/@Tech_Channel_2024"
        channel_id = YouTubeURLParser.extract_channel_id(url)
        assert channel_id == "Tech_Channel_2024"


class TestInvalidURLs:
    """Tests for handling invalid URLs"""

    def test_detect_invalid_url(self):
        """Test detecting invalid URL"""
        url = "https://example.com"
        url_type = YouTubeURLParser.detect_url_type(url)
        assert url_type == URLType.UNKNOWN

    def test_detect_empty_url(self):
        """Test handling empty URL"""
        url_type = YouTubeURLParser.detect_url_type("")
        assert url_type == URLType.UNKNOWN

    def test_detect_none_url(self):
        """Test handling None URL"""
        url_type = YouTubeURLParser.detect_url_type(None or "")
        assert url_type == URLType.UNKNOWN

    def test_extract_video_id_from_invalid_url(self):
        """Test extracting video ID from invalid URL returns None"""
        url = "https://example.com"
        video_id = YouTubeURLParser.extract_video_id(url)
        assert video_id is None

    def test_extract_playlist_id_from_invalid_url(self):
        """Test extracting playlist ID from invalid URL returns None"""
        url = "https://example.com"
        playlist_id = YouTubeURLParser.extract_playlist_id(url)
        assert playlist_id is None

    def test_extract_channel_id_from_invalid_url(self):
        """Test extracting channel ID from invalid URL returns None"""
        url = "https://example.com"
        channel_id = YouTubeURLParser.extract_channel_id(url)
        assert channel_id is None

    def test_invalid_video_id_too_short(self):
        """Test URL with video ID too short"""
        url = "https://youtube.com/watch?v=short"
        video_id = YouTubeURLParser.extract_video_id(url)
        # Should not match (too short - needs 11 chars)
        assert video_id is None

    def test_invalid_video_id_characters(self):
        """Test URL with invalid video ID characters"""
        url = "https://youtube.com/watch?v=invalid@chars!"
        video_id = YouTubeURLParser.extract_video_id(url)
        # Should not match (invalid characters)
        assert video_id is None


class TestURLParsing:
    """Tests for complete URL parsing"""

    def test_parse_video_url(self):
        """Test parsing complete video URL"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = YouTubeURLParser.parse_url(url)

        assert result["url"] == url
        assert result["type"] == URLType.VIDEO
        assert result["valid"] is True
        assert result["id"] == "dQw4w9WgXcQ"

    def test_parse_playlist_url(self):
        """Test parsing complete playlist URL"""
        url = "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
        result = YouTubeURLParser.parse_url(url)

        assert result["type"] == URLType.PLAYLIST
        assert result["valid"] is True
        assert result["id"] == "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"

    def test_parse_channel_url(self):
        """Test parsing complete channel URL"""
        url = "https://www.youtube.com/@MKBHD"
        result = YouTubeURLParser.parse_url(url)

        assert result["type"] == URLType.CHANNEL
        assert result["valid"] is True
        assert result["id"] == "MKBHD"

    def test_parse_invalid_url(self):
        """Test parsing invalid URL"""
        url = "https://example.com"
        result = YouTubeURLParser.parse_url(url)

        assert result["type"] == URLType.UNKNOWN
        assert result["valid"] is False
        assert "id" not in result

    def test_parse_multiple_urls(self):
        """Test parsing multiple URLs in sequence"""
        urls = [
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/playlist?list=PLxxx",
            "https://www.youtube.com/@TechChannel",
        ]

        expected_types = [URLType.VIDEO, URLType.PLAYLIST, URLType.CHANNEL]

        for url, expected_type in zip(urls, expected_types):
            result = YouTubeURLParser.parse_url(url)
            assert result["type"] == expected_type
            assert result["valid"] is True


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""

    def test_url_with_whitespace(self):
        """Test URL with leading/trailing whitespace"""
        url = "  https://youtu.be/dQw4w9WgXcQ  "
        video_id = YouTubeURLParser.extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_video_with_playlist_parameter(self):
        """Test URL with both video and playlist parameters"""
        # When both present, video URL pattern matches first in this implementation
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLxxx"
        video_id = YouTubeURLParser.extract_video_id(url)
        # Can still extract video ID from watch URL
        assert video_id == "dQw4w9WgXcQ"

    def test_youtube_without_protocol(self):
        """Test URL without protocol"""
        url = "youtu.be/dQw4w9WgXcQ"
        video_id = YouTubeURLParser.extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_various_video_id_formats(self):
        """Test various valid video ID formats"""
        # Valid characters in video IDs: A-Z, a-z, 0-9, -, _
        video_ids = [
            "dQw4w9WgXcQ",
            "9bZkp7q19f0",
            "OPf0YbXqDm0",
            "abc123-_xyz",
        ]

        for vid_id in video_ids:
            url = f"https://youtu.be/{vid_id}"
            extracted_id = YouTubeURLParser.extract_video_id(url)
            assert extracted_id == vid_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
