"""
File-based metadata storage system for YouTube channels, playlists, and videos
Saves metadata in both JSON and Markdown formats
"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class MetadataStore:
    """Manages file-based storage for YouTube metadata"""

    def __init__(self, base_path: str = "/app/metadata"):
        """Initialize metadata store

        Args:
            base_path: Base directory for storing metadata
        """
        self.base_path = Path(base_path)
        self._init_directories()

    def _init_directories(self):
        """Initialize required directory structure"""
        dirs = [
            self.base_path,
            self.base_path / "channels",
            self.base_path / "playlists",
            self.base_path / "videos",
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✓ Directory ready: {dir_path}")

    def save_channel_metadata(
        self,
        channel_id: str,
        channel_data: Dict[str, Any],
    ) -> Dict[str, Path]:
        """Save channel metadata to JSON and Markdown

        Args:
            channel_id: YouTube channel ID
            channel_data: Channel metadata dict

        Returns:
            Dict with paths to saved files
        """
        # Add metadata timestamps
        channel_data = {
            **channel_data,
            "_saved_at": datetime.now().isoformat(),
            "_type": "channel",
        }

        # Save JSON
        json_path = self.base_path / "channels" / f"channel_{channel_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(channel_data, f, indent=2, ensure_ascii=False)

        # Save Markdown
        md_path = self.base_path / "channels" / f"channel_{channel_id}.md"
        md_content = self._generate_channel_markdown(channel_data)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        logger.info(f"Saved channel metadata: {channel_id}")
        return {"json": json_path, "markdown": md_path}

    def save_playlist_metadata(
        self,
        playlist_id: str,
        playlist_data: Dict[str, Any],
    ) -> Dict[str, Path]:
        """Save playlist metadata to JSON and Markdown

        Args:
            playlist_id: YouTube playlist ID
            playlist_data: Playlist metadata dict

        Returns:
            Dict with paths to saved files
        """
        playlist_data = {
            **playlist_data,
            "_saved_at": datetime.now().isoformat(),
            "_type": "playlist",
        }

        json_path = self.base_path / "playlists" / f"playlist_{playlist_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(playlist_data, f, indent=2, ensure_ascii=False)

        md_path = self.base_path / "playlists" / f"playlist_{playlist_id}.md"
        md_content = self._generate_playlist_markdown(playlist_data)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        logger.info(f"Saved playlist metadata: {playlist_id}")
        return {"json": json_path, "markdown": md_path}

    def save_video_metadata(
        self,
        video_id: str,
        video_data: Dict[str, Any],
    ) -> Dict[str, Path]:
        """Save video metadata to JSON and Markdown

        Args:
            video_id: YouTube video ID
            video_data: Video metadata dict

        Returns:
            Dict with paths to saved files
        """
        video_data = {
            **video_data,
            "_saved_at": datetime.now().isoformat(),
            "_type": "video",
        }

        json_path = self.base_path / "videos" / f"video_{video_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(video_data, f, indent=2, ensure_ascii=False)

        md_path = self.base_path / "videos" / f"video_{video_id}.md"
        md_content = self._generate_video_markdown(video_data)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        logger.info(f"Saved video metadata: {video_id}")
        return {"json": json_path, "markdown": md_path}

    def load_channel_metadata(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Load channel metadata from JSON

        Args:
            channel_id: YouTube channel ID

        Returns:
            Channel metadata dict or None if not found
        """
        json_path = self.base_path / "channels" / f"channel_{channel_id}.json"
        if not json_path.exists():
            return None

        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_playlist_metadata(self, playlist_id: str) -> Optional[Dict[str, Any]]:
        """Load playlist metadata from JSON

        Args:
            playlist_id: YouTube playlist ID

        Returns:
            Playlist metadata dict or None if not found
        """
        json_path = self.base_path / "playlists" / f"playlist_{playlist_id}.json"
        if not json_path.exists():
            return None

        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_video_metadata(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Load video metadata from JSON

        Args:
            video_id: YouTube video ID

        Returns:
            Video metadata dict or None if not found
        """
        json_path = self.base_path / "videos" / f"video_{video_id}.json"
        if not json_path.exists():
            return None

        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_channel_ids(self) -> List[str]:
        """List all saved channel IDs

        Returns:
            List of channel IDs
        """
        channels_dir = self.base_path / "channels"
        channel_ids = []
        for json_file in channels_dir.glob("channel_*.json"):
            channel_id = json_file.stem.replace("channel_", "")
            channel_ids.append(channel_id)
        return sorted(channel_ids)

    def list_playlist_ids(self) -> List[str]:
        """List all saved playlist IDs

        Returns:
            List of playlist IDs
        """
        playlists_dir = self.base_path / "playlists"
        playlist_ids = []
        for json_file in playlists_dir.glob("playlist_*.json"):
            playlist_id = json_file.stem.replace("playlist_", "")
            playlist_ids.append(playlist_id)
        return sorted(playlist_ids)

    def list_video_ids(self) -> List[str]:
        """List all saved video IDs

        Returns:
            List of video IDs
        """
        videos_dir = self.base_path / "videos"
        video_ids = []
        for json_file in videos_dir.glob("video_*.json"):
            video_id = json_file.stem.replace("video_", "")
            video_ids.append(video_id)
        return sorted(video_ids)

    def channel_exists(self, channel_id: str) -> bool:
        """Check if channel metadata exists

        Args:
            channel_id: YouTube channel ID

        Returns:
            True if channel metadata exists
        """
        json_path = self.base_path / "channels" / f"channel_{channel_id}.json"
        return json_path.exists()

    def playlist_exists(self, playlist_id: str) -> bool:
        """Check if playlist metadata exists

        Args:
            playlist_id: YouTube playlist ID

        Returns:
            True if playlist metadata exists
        """
        json_path = self.base_path / "playlists" / f"playlist_{playlist_id}.json"
        return json_path.exists()

    def video_exists(self, video_id: str) -> bool:
        """Check if video metadata exists

        Args:
            video_id: YouTube video ID

        Returns:
            True if video metadata exists
        """
        json_path = self.base_path / "videos" / f"video_{video_id}.json"
        return json_path.exists()

    @staticmethod
    def _generate_channel_markdown(channel_data: Dict[str, Any]) -> str:
        """Generate Markdown representation of channel metadata

        Args:
            channel_data: Channel metadata dict

        Returns:
            Markdown formatted string
        """
        title = channel_data.get("title", "Unknown Channel")
        channel_id = channel_data.get("id", "Unknown")
        description = channel_data.get("description", "No description")
        playlist_count = channel_data.get("playlist_count", 0)
        video_count = channel_data.get("video_count", 0)

        md = f"""# Channel: {title}

## Metadata

- **Channel ID**: {channel_id}
- **Playlists**: {playlist_count}
- **Videos**: {video_count}

## Description

{description}

---

*Metadata extracted and saved for offline reference*
"""
        return md

    @staticmethod
    def _generate_playlist_markdown(playlist_data: Dict[str, Any]) -> str:
        """Generate Markdown representation of playlist metadata

        Args:
            playlist_data: Playlist metadata dict

        Returns:
            Markdown formatted string
        """
        title = playlist_data.get("title", "Unknown Playlist")
        playlist_id = playlist_data.get("id", "Unknown")
        channel_title = playlist_data.get("channel", "Unknown")
        video_count = playlist_data.get("video_count", 0)
        description = playlist_data.get("description", "No description")

        md = f"""# Playlist: {title}

## Metadata

- **Playlist ID**: {playlist_id}
- **Channel**: {channel_title}
- **Videos**: {video_count}

## Description

{description}

---

*Metadata extracted and saved for offline reference*
"""
        return md

    @staticmethod
    def _generate_video_markdown(video_data: Dict[str, Any]) -> str:
        """Generate Markdown representation of video metadata

        Args:
            video_data: Video metadata dict

        Returns:
            Markdown formatted string
        """
        title = video_data.get("title", "Unknown Video")
        video_id = video_data.get("id", "Unknown")
        channel_title = video_data.get("uploader", "Unknown")
        duration = video_data.get("duration", 0)
        description = video_data.get("description", "No description")

        duration_str = f"{duration // 60}:{duration % 60:02d}"

        md = f"""# Video: {title}

## Metadata

- **Video ID**: {video_id}
- **Uploader**: {channel_title}
- **Duration**: {duration_str}

## Description

{description}

---

*Metadata extracted and saved for offline reference*
"""
        return md
