"""
YouTube data extraction using yt-dlp
Extracts video, playlist, and channel metadata
And transcribes audio using WhisperX
"""
import json
import logging
from typing import Optional, List, Dict, Any, Union
import re
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import socket
import yt_dlp
import subprocess
import os
import tempfile
from datetime import datetime

logger = logging.getLogger(__name__)


class ErrorType(str, Enum):
    """Types of errors that can occur during extraction"""
    TIMEOUT = "timeout"                       # Network timeout
    NOT_FOUND = "not_found"                   # Video/playlist/channel not found (404)
    PRIVATE = "private"                       # Content is private
    DELETED = "deleted"                       # Content has been deleted
    RESTRICTED = "age_restricted"             # Age-restricted content
    RATE_LIMITED = "rate_limited"             # HTTP 429: Too many requests
    FORBIDDEN = "forbidden"                   # HTTP 403: Access forbidden
    CONNECTION_ERROR = "connection_error"     # Connection refused, reset, etc.
    INVALID_ID = "invalid_id"                 # Invalid video/playlist ID format
    NETWORK_ERROR = "network_error"           # General network error
    DATA_ERROR = "data_error"                 # Malformed or incomplete data
    UNKNOWN = "unknown"                       # Unknown error


@dataclass
class ExtractionError:
    """Error information from extraction"""
    error_type: ErrorType
    message: str
    retryable: bool

    def __repr__(self):
        return f"ExtractionError({self.error_type}: {self.message}, retryable={self.retryable})"


@dataclass
class ProcessingResult:
    """Result from video transcription"""
    status: str  # "success" or "failed"
    video_id: str
    video_title: str
    transcript_path: Optional[str] = None  # Path to markdown transcript
    metadata_path: Optional[str] = None  # Path to metadata JSON
    output_dir: Optional[str] = None  # Directory containing all output files
    duration: float = 0.0  # Video duration in seconds
    language: str = "en"  # Detected/used language
    error_message: Optional[str] = None  # Error message if failed
    speaker_count: int = 0  # Number of unique speakers detected
    word_count: int = 0  # Word count in transcript
    processing_time: float = 0.0  # Time taken to process in seconds

    def __repr__(self):
        if self.status == "success":
            return f"ProcessingResult(status={self.status}, video={self.video_title}, speakers={self.speaker_count})"
        else:
            return f"ProcessingResult(status=failed, error={self.error_message})"


class YouTubeExtractor:
    """Extract YouTube video, playlist, and channel data, and transcribe audio"""

    def __init__(self):
        """Initialize extractor with yt-dlp options"""
        self.ydl_opts = {
            'quiet': False,
            'no_warnings': False,
            'extract_flat': True,
            'skip_download': True,
        }
        # Get HF token from environment
        self.hf_token = os.getenv("HF_TOKEN")
        self.language = os.getenv("LANGUAGE", "en")
        self.compute_type = os.getenv("COMPUTE_TYPE", "int8")

    def process_video(self, video_url: str) -> ProcessingResult:
        """
        Download audio from YouTube video and transcribe using WhisperX

        Args:
            video_url: Full YouTube URL

        Returns:
            ProcessingResult with transcript path and metadata
        """
        import time
        start_time = time.time()

        try:
            # Extract video ID from URL
            video_id = self._extract_video_id(video_url)
            if not video_id:
                return ProcessingResult(
                    status="failed",
                    video_id="unknown",
                    video_title="unknown",
                    error_message="Could not extract video ID from URL"
                )

            logger.info(f"Processing video: {video_url}")

            # Create output directory
            output_dir = Path(f"/app/transcripts/{video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Output directory: {output_dir}")

            # Download audio from YouTube
            audio_path = self._download_audio(video_url, output_dir)
            if not audio_path:
                return ProcessingResult(
                    status="failed",
                    video_id=video_id,
                    video_title="unknown",
                    error_message="Failed to download audio from YouTube"
                )

            logger.info(f"Downloaded audio: {audio_path}")

            # Get video title and duration
            video_title, duration = self._get_video_info(video_url)

            # Transcribe using WhisperX
            transcript_data = self._transcribe_with_whisperx(str(audio_path), output_dir)
            if not transcript_data:
                return ProcessingResult(
                    status="failed",
                    video_id=video_id,
                    video_title=video_title or "unknown",
                    error_message="WhisperX transcription failed"
                )

            logger.info(f"Transcription complete: {len(transcript_data.get('segments', []))} segments")

            # Create markdown transcript
            transcript_path = self._create_transcript_markdown(video_id, video_title, transcript_data, output_dir)
            if not transcript_path:
                return ProcessingResult(
                    status="failed",
                    video_id=video_id,
                    video_title=video_title or "unknown",
                    error_message="Failed to create transcript markdown"
                )

            # Save full metadata
            metadata_path = output_dir / "metadata.json"
            metadata = {
                "video_id": video_id,
                "video_title": video_title,
                "duration": duration,
                "language": self.language,
                "processed_at": datetime.now().isoformat(),
                "speaker_count": len(set(seg.get("speaker", "unknown") for seg in transcript_data.get("segments", []))),
                "segments": transcript_data.get("segments", []),
            }
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            processing_time = time.time() - start_time

            result = ProcessingResult(
                status="success",
                video_id=video_id,
                video_title=video_title or "Unknown",
                transcript_path=str(transcript_path),
                metadata_path=str(metadata_path),
                output_dir=str(output_dir),
                duration=duration or 0.0,
                language=self.language,
                speaker_count=metadata.get("speaker_count", 0),
                word_count=self._count_words(transcript_data),
                processing_time=processing_time,
            )

            logger.info(f"✓ Transcription successful: {result}")
            return result

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"✗ Transcription failed: {str(e)}", exc_info=True)
            return ProcessingResult(
                status="failed",
                video_id=self._extract_video_id(video_url) or "unknown",
                video_title="unknown",
                error_message=str(e),
                processing_time=processing_time,
            )

    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
            r'(?:youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'(?:youtube\.com\/v\/)([a-zA-Z0-9_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def _download_audio(self, video_url: str, output_dir: Path) -> Optional[Path]:
        """Download audio from YouTube video"""
        try:
            audio_path = output_dir / "audio.mp3"
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': str(output_dir / 'audio'),
                'quiet': True,
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Downloading audio from {video_url}...")
                ydl.extract_info(video_url, download=True)

            if audio_path.exists():
                return audio_path
            return None

        except Exception as e:
            logger.error(f"Failed to download audio: {str(e)}")
            return None

    def _get_video_info(self, video_url: str) -> tuple[Optional[str], Optional[float]]:
        """Get video title and duration"""
        try:
            ydl_opts = {'quiet': True, 'no_warnings': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return info.get("title"), info.get("duration")
        except Exception as e:
            logger.error(f"Failed to get video info: {str(e)}")
            return None, None

    def _transcribe_with_whisperx(self, audio_path: str, output_dir: Path) -> Optional[Dict[str, Any]]:
        """Transcribe audio using WhisperX"""
        try:
            logger.info(f"Starting WhisperX transcription...")

            # Build WhisperX command
            cmd = [
                "whisperx",
                audio_path,
                "--model", "base",
                "--language", self.language,
                "--compute_type", self.compute_type,
                "--output_format", "json",
                "--output_dir", str(output_dir),
                "--vad_method", "silero",  # Use Silero VAD to avoid PyTorch 2.6 weights_only issue with PyAnnote
            ]

            # Add HF token if available for diarization
            if self.hf_token:
                cmd.extend(["--hf_token", self.hf_token])

            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)

            if result.returncode != 0:
                logger.error(f"WhisperX failed: {result.stderr}")
                return None

            # Load the JSON output
            json_output = output_dir / f"{Path(audio_path).stem}.json"
            if json_output.exists():
                with open(json_output, 'r', encoding='utf-8') as f:
                    return json.load(f)

            logger.error("WhisperX did not produce JSON output")
            return None

        except subprocess.TimeoutExpired:
            logger.error("WhisperX transcription timed out (>1200s/20min)")
            return None
        except Exception as e:
            logger.error(f"WhisperX transcription failed: {str(e)}")
            return None

    def _create_transcript_markdown(self, video_id: str, title: str, transcript_data: Dict[str, Any], output_dir: Path) -> Optional[Path]:
        """Create markdown transcript from WhisperX JSON output"""
        try:
            transcript_path = output_dir / "transcript.md"

            # Group segments by speaker
            segments_by_speaker = {}
            for segment in transcript_data.get("segments", []):
                speaker = segment.get("speaker", "Unknown")
                if speaker not in segments_by_speaker:
                    segments_by_speaker[speaker] = []
                segments_by_speaker[speaker].append(segment)

            # Build markdown
            md_lines = [
                f"# Transcript: {title}",
                "",
                f"**Video ID**: {video_id}",
                f"**Processed**: {datetime.now().isoformat()}",
                "",
                "## Transcript by Speaker",
                "",
            ]

            for speaker, segments in segments_by_speaker.items():
                md_lines.append(f"### {speaker}")
                md_lines.append("")
                for segment in segments:
                    start = self._format_timestamp(segment.get("start", 0))
                    text = segment.get("text", "").strip()
                    if text:
                        md_lines.append(f"**[{start}]** {text}")
                md_lines.append("")

            # Full transcript
            md_lines.extend([
                "",
                "## Full Transcript",
                "",
            ])
            for segment in transcript_data.get("segments", []):
                start = self._format_timestamp(segment.get("start", 0))
                text = segment.get("text", "").strip()
                speaker = segment.get("speaker", "Unknown")
                if text:
                    md_lines.append(f"**[{start}] {speaker}**: {text}")

            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(md_lines))

            logger.info(f"Created transcript: {transcript_path}")
            return transcript_path

        except Exception as e:
            logger.error(f"Failed to create transcript markdown: {str(e)}")
            return None

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds to HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    @staticmethod
    def _count_words(transcript_data: Dict[str, Any]) -> int:
        """Count words in transcript"""
        total = 0
        for segment in transcript_data.get("segments", []):
            text = segment.get("text", "").strip()
            if text:
                total += len(text.split())
        return total

    def extract_video(self, video_id: str) -> Union[Dict[str, Any], ExtractionError]:
        """
        Extract single video metadata

        Args:
            video_id: YouTube video ID

        Returns:
            Video metadata dictionary or ExtractionError if failed
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

        except socket.timeout:
            error = ExtractionError(ErrorType.TIMEOUT, "Network request timed out", retryable=True)
            logger.error(f"✗ {error}")
            return error
        except socket.error as e:
            error = ExtractionError(ErrorType.CONNECTION_ERROR, f"Connection error: {str(e)}", retryable=True)
            logger.error(f"✗ {error}")
            return error
        except Exception as e:
            error_msg = str(e).lower()

            # Classify error based on message content
            if "video not found" in error_msg or "404" in error_msg:
                error = ExtractionError(ErrorType.NOT_FOUND, f"Video not found: {video_id}", retryable=False)
            elif "private video" in error_msg or "private" in error_msg:
                error = ExtractionError(ErrorType.PRIVATE, "Video is private", retryable=False)
            elif "has been removed" in error_msg or "deleted" in error_msg:
                error = ExtractionError(ErrorType.DELETED, "Video has been deleted", retryable=False)
            elif "age restricted" in error_msg or "age-restricted" in error_msg:
                error = ExtractionError(ErrorType.RESTRICTED, "Video is age-restricted", retryable=False)
            elif "429" in error_msg or "rate limit" in error_msg:
                error = ExtractionError(ErrorType.RATE_LIMITED, "Rate limited by YouTube", retryable=True)
            elif "403" in error_msg or "forbidden" in error_msg:
                error = ExtractionError(ErrorType.FORBIDDEN, "Access forbidden", retryable=False)
            elif "invalid" in error_msg and "id" in error_msg:
                error = ExtractionError(ErrorType.INVALID_ID, f"Invalid video ID: {video_id}", retryable=False)
            elif isinstance(e, (json.JSONDecodeError, ValueError)):
                error = ExtractionError(ErrorType.DATA_ERROR, f"Malformed data: {str(e)}", retryable=False)
            else:
                error = ExtractionError(ErrorType.UNKNOWN, f"Unknown error: {str(e)}", retryable=True)

            logger.error(f"✗ {error}")
            return error

    def extract_playlist(self, playlist_id: str) -> Union[Dict[str, Any], ExtractionError]:
        """
        Extract playlist metadata and video list

        Args:
            playlist_id: YouTube playlist ID

        Returns:
            Playlist metadata with video list or ExtractionError if failed
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

        except socket.timeout:
            error = ExtractionError(ErrorType.TIMEOUT, "Network request timed out", retryable=True)
            logger.error(f"✗ {error}")
            return error
        except socket.error as e:
            error = ExtractionError(ErrorType.CONNECTION_ERROR, f"Connection error: {str(e)}", retryable=True)
            logger.error(f"✗ {error}")
            return error
        except Exception as e:
            error_msg = str(e).lower()

            # Classify error based on message content
            if "not found" in error_msg or "404" in error_msg:
                error = ExtractionError(ErrorType.NOT_FOUND, f"Playlist not found: {playlist_id}", retryable=False)
            elif "private" in error_msg:
                error = ExtractionError(ErrorType.PRIVATE, "Playlist is private", retryable=False)
            elif "has been removed" in error_msg or "deleted" in error_msg:
                error = ExtractionError(ErrorType.DELETED, "Playlist has been deleted", retryable=False)
            elif "429" in error_msg or "rate limit" in error_msg:
                error = ExtractionError(ErrorType.RATE_LIMITED, "Rate limited by YouTube", retryable=True)
            elif "403" in error_msg or "forbidden" in error_msg:
                error = ExtractionError(ErrorType.FORBIDDEN, "Access forbidden", retryable=False)
            elif "invalid" in error_msg and "id" in error_msg:
                error = ExtractionError(ErrorType.INVALID_ID, f"Invalid playlist ID: {playlist_id}", retryable=False)
            elif isinstance(e, (json.JSONDecodeError, ValueError)):
                error = ExtractionError(ErrorType.DATA_ERROR, f"Malformed data: {str(e)}", retryable=False)
            else:
                error = ExtractionError(ErrorType.UNKNOWN, f"Unknown error: {str(e)}", retryable=True)

            logger.error(f"✗ {error}")
            return error

    def extract_channel(self, channel_id: str) -> Union[Dict[str, Any], ExtractionError]:
        """
        Extract channel metadata and all playlists

        Args:
            channel_id: YouTube channel ID or handle

        Returns:
            Channel metadata with playlists or ExtractionError if failed
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

        except socket.timeout:
            error = ExtractionError(ErrorType.TIMEOUT, "Network request timed out", retryable=True)
            logger.error(f"✗ {error}")
            return error
        except socket.error as e:
            error = ExtractionError(ErrorType.CONNECTION_ERROR, f"Connection error: {str(e)}", retryable=True)
            logger.error(f"✗ {error}")
            return error
        except Exception as e:
            error_msg = str(e).lower()

            # Classify error based on message content
            if "not found" in error_msg or "404" in error_msg:
                error = ExtractionError(ErrorType.NOT_FOUND, f"Channel not found: {channel_id}", retryable=False)
            elif "suspended" in error_msg or "terminated" in error_msg:
                error = ExtractionError(ErrorType.DELETED, "Channel has been terminated", retryable=False)
            elif "429" in error_msg or "rate limit" in error_msg:
                error = ExtractionError(ErrorType.RATE_LIMITED, "Rate limited by YouTube", retryable=True)
            elif "403" in error_msg or "forbidden" in error_msg:
                error = ExtractionError(ErrorType.FORBIDDEN, "Access forbidden", retryable=False)
            elif "invalid" in error_msg and "id" in error_msg:
                error = ExtractionError(ErrorType.INVALID_ID, f"Invalid channel ID: {channel_id}", retryable=False)
            elif isinstance(e, (json.JSONDecodeError, ValueError)):
                error = ExtractionError(ErrorType.DATA_ERROR, f"Malformed data: {str(e)}", retryable=False)
            else:
                error = ExtractionError(ErrorType.UNKNOWN, f"Unknown error: {str(e)}", retryable=True)

            logger.error(f"✗ {error}")
            return error

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
