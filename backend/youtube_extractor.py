"""
YouTube data extraction using yt-dlp
Extracts video, playlist, and channel metadata
"""
import json
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
import yt_dlp

logger = logging.getLogger(__name__)


class YouTubeExtractor:
    """Extract YouTube video, playlist, and channel data"""

    def __init__(self):
        """Initialize extractor with yt-dlp options"""
        self.ydl_opts = {
            'quiet': False,
            'no_warnings': False,
            'extract_flat': True,
            'skip_download': True,
        }

    def extract_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Extract single video metadata

        Args:
            video_id: YouTube video ID

        Returns:
            Video metadata dictionary or None if failed
        """
        url = f"https://www.youtube.com/watch?v={video_id}"

        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            video_data = {
                "id": info.get("id"),
                "title": info.get("title"),
                "uploader": info.get("uploader"),
                "uploader_id": info.get("uploader_id"),
                "duration": info.get("duration"),
                "description": info.get("description"),
                "view_count": info.get("view_count"),
                "upload_date": info.get("upload_date"),
                "thumbnail": info.get("thumbnail"),
            }

            logger.info(f"✓ Extracted video: {video_data['title']} ({video_id})")
            return video_data

        except Exception as e:
            logger.error(f"✗ Failed to extract video {video_id}: {str(e)}")
            return None

    def extract_playlist(self, playlist_id: str) -> Optional[Dict[str, Any]]:
        """
        Extract playlist metadata and video list

        Args:
            playlist_id: YouTube playlist ID

        Returns:
            Playlist metadata with video list or None if failed
        """
        url = f"https://www.youtube.com/playlist?list={playlist_id}"

        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            videos = []
            for entry in (info.get("entries") or []):
                if entry:
                    videos.append({
                        "id": entry.get("id"),
                        "title": entry.get("title"),
                        "uploader": entry.get("uploader"),
                        "duration": entry.get("duration"),
                    })

            playlist_data = {
                "id": playlist_id,
                "title": info.get("title"),
                "uploader": info.get("uploader"),
                "description": info.get("description"),
                "video_count": len(videos),
                "videos": videos,
            }

            logger.info(f"✓ Extracted playlist: {playlist_data['title']} ({len(videos)} videos)")
            return playlist_data

        except Exception as e:
            logger.error(f"✗ Failed to extract playlist {playlist_id}: {str(e)}")
            return None

    def extract_channel(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Extract channel metadata and all playlists

        Args:
            channel_id: YouTube channel ID or handle

        Returns:
            Channel metadata with playlists or None if failed
        """
        # Support both channel ID (UC...) and handle (@...)
        if channel_id.startswith("@"):
            url = f"https://www.youtube.com/{channel_id}"
        else:
            url = f"https://www.youtube.com/channel/{channel_id}"

        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            playlists = []
            for entry in (info.get("entries") or []):
                if entry and entry.get("_type") == "playlist":
                    playlists.append({
                        "id": entry.get("id"),
                        "title": entry.get("title"),
                        "video_count": entry.get("playlist_count"),
                    })

            channel_data = {
                "id": info.get("id"),
                "title": info.get("title"),
                "description": info.get("description"),
                "subscriber_count": info.get("subscriber_count"),
                "video_count": info.get("video_count"),
                "playlist_count": len(playlists),
                "playlists": playlists,
            }

            logger.info(f"✓ Extracted channel: {channel_data['title']} ({len(playlists)} playlists)")
            return channel_data

        except Exception as e:
            logger.error(f"✗ Failed to extract channel {channel_id}: {str(e)}")
            return None

    def save_as_json(self, data: Dict[str, Any], filepath: str) -> bool:
        """
        Save metadata as JSON

        Args:
            data: Metadata dictionary
            filepath: Output filepath

        Returns:
            True if successful, False otherwise
        """
        try:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"✓ Saved JSON: {filepath}")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to save JSON {filepath}: {str(e)}")
            return False

    def save_as_markdown(self, data: Dict[str, Any], filepath: str, data_type: str = "video") -> bool:
        """
        Save metadata as Markdown

        Args:
            data: Metadata dictionary
            filepath: Output filepath
            data_type: Type of data (video, playlist, channel)

        Returns:
            True if successful, False otherwise
        """
        try:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)

            if data_type == "video":
                md_content = self._generate_video_markdown(data)
            elif data_type == "playlist":
                md_content = self._generate_playlist_markdown(data)
            elif data_type == "channel":
                md_content = self._generate_channel_markdown(data)
            else:
                md_content = json.dumps(data, indent=2, ensure_ascii=False)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md_content)

            logger.info(f"✓ Saved Markdown: {filepath}")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to save Markdown {filepath}: {str(e)}")
            return False

    @staticmethod
    def _generate_video_markdown(data: Dict[str, Any]) -> str:
        """Generate Markdown for video metadata"""
        view_count = data.get('view_count')
        view_str = f"{view_count:,}" if view_count else "Unknown"

        md = f"""# Video: {data.get('title', 'Unknown')}

## Metadata

- **Video ID**: {data.get('id')}
- **Uploader**: {data.get('uploader')}
- **Duration**: {data.get('duration')}s
- **Views**: {view_str}
- **Uploaded**: {data.get('upload_date')}

## Description

{data.get('description', 'No description')}

---

*Metadata extracted with yt-dlp*
"""
        return md

    @staticmethod
    def _generate_playlist_markdown(data: Dict[str, Any]) -> str:
        """Generate Markdown for playlist metadata"""
        videos_md = "\n".join([
            f"- {v['title']} ({v['id']})"
            for v in data.get('videos', [])[:10]
        ])

        md = f"""# Playlist: {data.get('title', 'Unknown')}

## Metadata

- **Playlist ID**: {data.get('id')}
- **Uploader**: {data.get('uploader')}
- **Video Count**: {data.get('video_count')}

## Description

{data.get('description', 'No description')}

## Videos (first 10)

{videos_md}

---

*Metadata extracted with yt-dlp*
"""
        return md

    @staticmethod
    def _generate_channel_markdown(data: Dict[str, Any]) -> str:
        """Generate Markdown for channel metadata"""
        playlists_md = "\n".join([
            f"- {p['title']} ({p['id']}) - {p.get('video_count', 0)} videos"
            for p in data.get('playlists', [])[:10]
        ])

        md = f"""# Channel: {data.get('title', 'Unknown')}

## Metadata

- **Channel ID**: {data.get('id')}
- **Subscribers**: {data.get('subscriber_count', 0)}
- **Total Videos**: {data.get('video_count', 0)}
- **Playlists**: {data.get('playlist_count', 0)}

## Description

{data.get('description', 'No description')}

## Playlists (first 10)

{playlists_md}

---

*Metadata extracted with yt-dlp*
"""
        return md
