"""
YouTube URL parsing and detection utilities
Detects video, playlist, and channel URLs and extracts IDs
"""
import re
import logging
from typing import Optional, Literal
from enum import Enum

logger = logging.getLogger(__name__)


class URLType(str, Enum):
    """Types of YouTube URLs"""
    VIDEO = "video"
    PLAYLIST = "playlist"
    CHANNEL = "channel"
    UNKNOWN = "unknown"


class YouTubeURLParser:
    """Parse and detect YouTube URL types"""

    # Regex patterns for different URL formats
    PATTERNS = {
        # Standard video URLs
        'video_standard': r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        # Short video URLs
        'video_short': r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',
        # Playlist URLs
        'playlist': r'(?:https?://)?(?:www\.)?youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)',
        # Channel by name
        'channel_handle': r'(?:https?://)?(?:www\.)?youtube\.com/@([a-zA-Z0-9_-]+)',
        # Channel by ID
        'channel_id': r'(?:https?://)?(?:www\.)?youtube\.com/channel/([a-zA-Z0-9_-]+)',
        # User/legacy channel
        'channel_user': r'(?:https?://)?(?:www\.)?youtube\.com/user/([a-zA-Z0-9_-]+)',
    }

    @staticmethod
    def detect_url_type(url: str) -> URLType:
        """
        Detect the type of YouTube URL

        Args:
            url: YouTube URL to analyze

        Returns:
            URLType enum value
        """
        if not url:
            return URLType.UNKNOWN

        url = url.strip()

        # Check for playlist parameter first (has priority)
        if YouTubeURLParser._matches_pattern(url, 'playlist'):
            return URLType.PLAYLIST

        # Check video URLs
        if (YouTubeURLParser._matches_pattern(url, 'video_standard') or
            YouTubeURLParser._matches_pattern(url, 'video_short')):
            return URLType.VIDEO

        # Check channel URLs
        if (YouTubeURLParser._matches_pattern(url, 'channel_handle') or
            YouTubeURLParser._matches_pattern(url, 'channel_id') or
            YouTubeURLParser._matches_pattern(url, 'channel_user')):
            return URLType.CHANNEL

        return URLType.UNKNOWN

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL

        Args:
            url: YouTube video URL

        Returns:
            Video ID or None if not found
        """
        if not url:
            return None

        url = url.strip()

        # Try standard YouTube URL format
        match = re.search(YouTubeURLParser.PATTERNS['video_standard'], url)
        if match:
            return match.group(1)

        # Try short YouTube URL format
        match = re.search(YouTubeURLParser.PATTERNS['video_short'], url)
        if match:
            return match.group(1)

        return None

    @staticmethod
    def extract_playlist_id(url: str) -> Optional[str]:
        """
        Extract playlist ID from YouTube URL

        Args:
            url: YouTube playlist URL

        Returns:
            Playlist ID or None if not found
        """
        if not url:
            return None

        url = url.strip()

        match = re.search(YouTubeURLParser.PATTERNS['playlist'], url)
        if match:
            return match.group(1)

        return None

    @staticmethod
    def extract_channel_id(url: str) -> Optional[str]:
        """
        Extract channel identifier from YouTube URL

        Args:
            url: YouTube channel URL

        Returns:
            Channel ID, handle, or username, or None if not found
        """
        if not url:
            return None

        url = url.strip()

        # Try channel handle (@name format)
        match = re.search(YouTubeURLParser.PATTERNS['channel_handle'], url)
        if match:
            return match.group(1)

        # Try channel ID format
        match = re.search(YouTubeURLParser.PATTERNS['channel_id'], url)
        if match:
            return match.group(1)

        # Try user/legacy format
        match = re.search(YouTubeURLParser.PATTERNS['channel_user'], url)
        if match:
            return match.group(1)

        return None

    @staticmethod
    def _matches_pattern(url: str, pattern_name: str) -> bool:
        """Check if URL matches a pattern"""
        pattern = YouTubeURLParser.PATTERNS.get(pattern_name)
        if not pattern:
            return False
        return bool(re.search(pattern, url))

    @staticmethod
    def parse_url(url: str) -> dict:
        """
        Parse a YouTube URL and extract all information

        Args:
            url: YouTube URL to parse

        Returns:
            Dictionary with URL type and extracted ID
        """
        url_type = YouTubeURLParser.detect_url_type(url)

        result = {
            "url": url,
            "type": url_type,
            "valid": url_type != URLType.UNKNOWN,
        }

        if url_type == URLType.VIDEO:
            video_id = YouTubeURLParser.extract_video_id(url)
            result["id"] = video_id
        elif url_type == URLType.PLAYLIST:
            playlist_id = YouTubeURLParser.extract_playlist_id(url)
            result["id"] = playlist_id
        elif url_type == URLType.CHANNEL:
            channel_id = YouTubeURLParser.extract_channel_id(url)
            result["id"] = channel_id

        logger.info(f"Parsed URL: {url} -> Type: {url_type}, ID: {result.get('id')}")
        return result
