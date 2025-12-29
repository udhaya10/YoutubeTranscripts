"""
youtube_extractor.py

Core module for YouTube video extraction, processing, and transcription.
Handles:
  1. Link detection and validation
  2. Metadata extraction via yt-dlp
  3. Audio extraction
  4. Speech-to-text transcription via WhisperX
  5. Speaker diarization
  6. Output formatting (Markdown + JSON)
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs

import yt_dlp
from pydantic import BaseModel, ValidationError

# PyTorch 2.8+ compatibility: Allow omegaconf to be loaded by torch.load()
try:
    import torch
    from torch.serialization import add_safe_globals
    try:
        import omegaconf
        add_safe_globals([omegaconf.listconfig.ListConfig, omegaconf.dictconfig.DictConfig])
    except (ImportError, AttributeError):
        pass
except ImportError:
    pass


# ============================================================================
# DATA MODELS (Pydantic for type safety and validation)
# ============================================================================

class LinkInfo(BaseModel):
    """Represents parsed YouTube link metadata"""
    url: str
    link_type: str  # "VIDEO", "PLAYLIST", "CHANNEL", "INVALID"
    video_id: Optional[str] = None
    playlist_id: Optional[str] = None
    channel_id: Optional[str] = None
    valid: bool


class VideoMetadata(BaseModel):
    """Video metadata extracted via yt-dlp"""
    video_id: str
    title: str
    channel: str
    channel_id: str
    duration_seconds: int
    view_count: int
    upload_date: str
    description: str
    thumbnail: str
    available_subtitles: List[str]
    available_auto_captions: List[str]


class TranscriptEntry(BaseModel):
    """Single transcript entry with timestamp and speaker"""
    start: float  # Timestamp in seconds
    end: float
    text: str
    speaker: Optional[str] = None  # Speaker name (e.g., "Speaker 1")


class ProcessingResult(BaseModel):
    """Complete result of processing a single video"""
    video_id: str
    title: str
    status: str  # "success", "error", "skipped"
    metadata: Optional[VideoMetadata] = None
    transcript: Optional[List[TranscriptEntry]] = None
    transcript_text: Optional[str] = None
    output_dir: str
    error_message: Optional[str] = None
    processing_time_seconds: float


# ============================================================================
# LINK DETECTION & VALIDATION
# ============================================================================

class YouTubeLinkDetector:
    """Detects and validates YouTube URLs"""

    YOUTUBE_PATTERNS = {
        "watch": r"(?:youtube\.com\/watch\?v=|youtu\.be\/)([^\&\n\r]+)",
        "playlist": r"list=([a-zA-Z0-9_-]+)",
        "channel": r"channel/([a-zA-Z0-9_-]+)",
        "channel_handle": r"@([a-zA-Z0-9_-]+)",
    }

    @staticmethod
    def detect(url: str) -> LinkInfo:
        """
        Detects YouTube link type and extracts identifiers.

        Args:
            url: The URL string to analyze

        Returns:
            LinkInfo object with parsed information
        """
        url = url.strip()

        result = {
            "url": url,
            "link_type": "INVALID",
            "video_id": None,
            "playlist_id": None,
            "channel_id": None,
            "valid": False,
        }

        # Check for valid YouTube domain
        if not any(domain in url for domain in ["youtube.com", "youtu.be"]):
            return LinkInfo(**result)

        # Pattern 1: Video URL (with optional playlist)
        if "watch" in url or "youtu.be" in url:
            match = re.search(YouTubeLinkDetector.YOUTUBE_PATTERNS["watch"], url)
            if match:
                result["video_id"] = match.group(1)
                result["link_type"] = "VIDEO"
                result["valid"] = True

                # Check for playlist context
                if "list=" in url:
                    playlist_match = re.search(
                        YouTubeLinkDetector.YOUTUBE_PATTERNS["playlist"], url
                    )
                    if playlist_match:
                        result["playlist_id"] = playlist_match.group(1)
                        result["link_type"] = "PLAYLIST_ITEM"

        # Pattern 2: Playlist URL
        elif "playlist" in url:
            match = re.search(YouTubeLinkDetector.YOUTUBE_PATTERNS["playlist"], url)
            if match:
                result["playlist_id"] = match.group(1)
                result["link_type"] = "PLAYLIST"
                result["valid"] = True

        # Pattern 3: Channel URL (by ID)
        elif "channel/" in url:
            match = re.search(YouTubeLinkDetector.YOUTUBE_PATTERNS["channel"], url)
            if match:
                result["channel_id"] = match.group(1)
                result["link_type"] = "CHANNEL"
                result["valid"] = True

        # Pattern 4: Channel URL (by handle @username)
        elif "/@" in url:
            match = re.search(YouTubeLinkDetector.YOUTUBE_PATTERNS["channel_handle"], url)
            if match:
                result["channel_id"] = match.group(1)
                result["link_type"] = "CHANNEL_HANDLE"
                result["valid"] = True

        return LinkInfo(**result)


# ============================================================================
# METADATA EXTRACTION
# ============================================================================

class MetadataExtractor:
    """Extracts video metadata using yt-dlp"""

    @staticmethod
    def extract(video_url: str) -> Optional[VideoMetadata]:
        """
        Extract comprehensive metadata from a YouTube video using yt-dlp.

        Args:
            video_url: Full YouTube URL

        Returns:
            VideoMetadata object or None if extraction fails
        """
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,  # Don't download the video itself
            "extract_flat": False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)

                # Extract key fields
                metadata = VideoMetadata(
                    video_id=info.get("id", "unknown"),
                    title=info.get("title", "Unknown Title"),
                    channel=info.get("uploader", "Unknown Channel"),
                    channel_id=info.get("channel_id", "unknown"),
                    duration_seconds=info.get("duration", 0),
                    view_count=info.get("view_count", 0) or 0,
                    upload_date=info.get("upload_date", "unknown"),
                    description=info.get("description", "")[:500],  # Truncate long descriptions
                    thumbnail=info.get("thumbnail", ""),
                    available_subtitles=list(info.get("subtitles", {}).keys()),
                    available_auto_captions=list(
                        info.get("automatic_captions", {}).keys()
                    ),
                )

                return metadata

        except Exception as e:
            print(f"[ERROR] Failed to extract metadata: {str(e)}")
            return None


# ============================================================================
# AUDIO EXTRACTION
# ============================================================================

class AudioExtractor:
    """Extracts audio from YouTube videos"""

    @staticmethod
    def extract(video_url: str, output_path: str) -> Optional[str]:
        """
        Download audio from YouTube video as MP3.

        Args:
            video_url: Full YouTube URL
            output_path: Directory to save audio file

        Returns:
            Path to saved audio file, or None if extraction fails
        """
        # Ensure output directory exists
        Path(output_path).mkdir(parents=True, exist_ok=True)

        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": os.path.join(output_path, "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                audio_path = os.path.join(output_path, f"{info['id']}.mp3")

                # Wait for file to exist
                if os.path.exists(audio_path):
                    return audio_path
                else:
                    # Sometimes extension is different
                    import glob
                    files = glob.glob(os.path.join(output_path, f"{info['id']}.*"))
                    if files:
                        return files[0]

                return None

        except Exception as e:
            print(f"[ERROR] Failed to extract audio: {str(e)}")
            return None


# ============================================================================
# TRANSCRIPTION (WhisperX)
# ============================================================================

class TranscriptionEngine:
    """Handles speech-to-text transcription via WhisperX"""

    @staticmethod
    def _check_whisperx_installed() -> bool:
        """
        Verify that WhisperX is installed and accessible.

        Returns:
            True if WhisperX is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["whisperx", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    @staticmethod
    def _check_model_exists(model_name: str = "large-v3") -> bool:
        """
        Check if WhisperX model is cached locally.

        Args:
            model_name: Name of the model (default: large-v3)

        Returns:
            True if model exists in cache, False otherwise
        """
        # WhisperX models are cached in HuggingFace cache directory
        cache_dir = Path.home() / ".cache" / "huggingface"

        # Check if any whisper model exists in cache
        if cache_dir.exists():
            # Look for any whisper-related directory
            for item in cache_dir.iterdir():
                if "whisper" in item.name.lower() and item.is_dir():
                    return True

        return False

    @staticmethod
    def transcribe(
        audio_path: str,
        output_dir: str,
        language: str = "en",
        compute_type: str = "int8",
        enable_diarization: bool = True,
        hf_token: Optional[str] = None,
    ) -> Optional[List[TranscriptEntry]]:
        """
        Transcribe audio file using WhisperX with optional speaker diarization.

        Args:
            audio_path: Path to audio file
            output_dir: Directory to save transcription outputs
            language: Language code (default: en)
            compute_type: Computation type (int8, float32, float16)
            enable_diarization: Whether to perform speaker diarization
            hf_token: HuggingFace API token (required for diarization)

        Returns:
            List of TranscriptEntry objects, or None if transcription fails
        """

        # Verify WhisperX is installed
        if not TranscriptionEngine._check_whisperx_installed():
            print(
                "[ERROR] WhisperX is not installed. Run: pip install git+https://github.com/m-bain/whisperx.git"
            )
            return None

        # Warn if model doesn't exist (will download on first run)
        if not TranscriptionEngine._check_model_exists():
            print(
                "[INFO] WhisperX model not found locally. Will download on first run (~3GB)..."
            )

        # Build WhisperX command (use wrapper script for PyTorch 2.8+ compatibility)
        # First try the wrapper script, fall back to direct whisperx if not available
        if os.path.exists("/app/docker/whisperx-wrapper.py"):
            cmd = [
                "python3", "/app/docker/whisperx-wrapper.py",
                audio_path,
                "--model", "large-v3",
                "--language", language,
                "--compute_type", compute_type,
                "--output_dir", output_dir,
                "--output_format", "json",
            ]
        else:
            cmd = [
                "whisperx",
                audio_path,
                "--model", "large-v3",
                "--language", language,
                "--compute_type", compute_type,
                "--output_dir", output_dir,
                "--output_format", "json",
            ]

        # Add diarization if enabled and token provided
        if enable_diarization:
            if not hf_token:
                print(
                    "[WARNING] Diarization enabled but no HF token provided. Skipping speaker detection."
                )
            else:
                cmd.extend(["--diarize", "--hf_token", hf_token])

        try:
            print(f"[INFO] Starting transcription: {audio_path}")

            # PyTorch 2.8+ workaround: Patch torch.load to allow omegaconf before calling whisperx
            # This must happen before importing whisperx
            try:
                import torch.serialization
                import omegaconf.listconfig
                import omegaconf.dictconfig
                torch.serialization.add_safe_globals([
                    omegaconf.listconfig.ListConfig,
                    omegaconf.dictconfig.DictConfig
                ])
            except (ImportError, AttributeError):
                pass

            # Run whisperx
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

            if result.returncode != 0:
                print(f"[ERROR] WhisperX failed: {result.stderr}")
                return None

            # Read the generated JSON file
            json_output_path = Path(output_dir) / f"{Path(audio_path).stem}.json"

            if not json_output_path.exists():
                print(f"[ERROR] WhisperX did not produce output JSON")
                return None

            with open(json_output_path, "r") as f:
                whisperx_output = json.load(f)

            # Parse WhisperX output into TranscriptEntry objects
            entries = []
            for segment in whisperx_output.get("segments", []):
                entry = TranscriptEntry(
                    start=segment.get("start", 0),
                    end=segment.get("end", 0),
                    text=segment.get("text", "").strip(),
                    speaker=segment.get("speaker", None),
                )
                if entry.text:  # Only include non-empty entries
                    entries.append(entry)

            return entries

        except subprocess.TimeoutExpired:
            print("[ERROR] WhisperX transcription timed out (>1 hour)")
            return None
        except Exception as e:
            print(f"[ERROR] Transcription failed: {str(e)}")
            return None


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================

class OutputFormatter:
    """Formats transcription results for output"""

    @staticmethod
    def format_markdown(
        metadata: VideoMetadata, entries: List[TranscriptEntry]
    ) -> str:
        """
        Format transcript as readable Markdown.

        Args:
            metadata: Video metadata
            entries: List of transcript entries

        Returns:
            Formatted Markdown string
        """
        md = f"""# {metadata.title}

**Channel:** {metadata.channel}  
**Video ID:** {metadata.video_id}  
**Duration:** {metadata.duration_seconds // 60} minutes  
**Views:** {metadata.view_count:,}  
**Uploaded:** {metadata.upload_date}  

---

## Transcript

"""

        current_speaker = None

        for entry in entries:
            # Add speaker label if it changed
            if entry.speaker and entry.speaker != current_speaker:
                md += f"\n**{entry.speaker}:**\n\n"
                current_speaker = entry.speaker

            # Format timestamp
            minutes = int(entry.start) // 60
            seconds = int(entry.start) % 60
            timestamp = f"[{minutes:02d}:{seconds:02d}]"

            md += f"{timestamp} {entry.text}\n"

        md += f"""

---

*Transcript generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return md

    @staticmethod
    def format_json(
        metadata: VideoMetadata, entries: List[TranscriptEntry]
    ) -> str:
        """
        Format transcript as structured JSON.

        Args:
            metadata: Video metadata
            entries: List of transcript entries

        Returns:
            JSON string
        """
        data = {
            "metadata": metadata.dict(),
            "transcript": [entry.dict() for entry in entries],
            "generated_at": datetime.now().isoformat(),
        }
        return json.dumps(data, indent=2, ensure_ascii=False)


# ============================================================================
# MAIN ORCHESTRATOR
# ============================================================================

class YouTubeExtractor:
    """Main orchestrator for the entire extraction pipeline"""

    def __init__(
        self,
        output_base_dir: str = "./transcripts",
        language: str = "en",
        compute_type: str = "int8",
        enable_diarization: bool = True,
        hf_token: Optional[str] = None,
    ):
        """
        Initialize the extractor.

        Args:
            output_base_dir: Base directory for all outputs
            language: Language for transcription
            compute_type: WhisperX computation type
            enable_diarization: Enable speaker diarization
            hf_token: HuggingFace token for diarization
        """
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        self.language = language
        self.compute_type = compute_type
        self.enable_diarization = enable_diarization
        self.hf_token = hf_token

    def process_video(self, video_url: str) -> ProcessingResult:
        """
        Process a single YouTube video: extract metadata, audio, and transcribe.

        Args:
            video_url: Full YouTube URL

        Returns:
            ProcessingResult with status and data
        """
        start_time = datetime.now()

        # Step 1: Detect link type
        link_info = YouTubeLinkDetector.detect(video_url)
        if not link_info.valid or link_info.link_type == "INVALID":
            return ProcessingResult(
                video_id="unknown",
                title="Unknown",
                status="error",
                output_dir=str(self.output_base_dir),
                error_message=f"Invalid YouTube URL: {video_url}",
                processing_time_seconds=(datetime.now() - start_time).total_seconds(),
            )

        if link_info.link_type == "PLAYLIST":
            return ProcessingResult(
                video_id=link_info.playlist_id or "unknown",
                title="Playlist",
                status="skipped",
                output_dir=str(self.output_base_dir),
                error_message="Playlist detected. Use --process-playlist flag to handle playlists.",
                processing_time_seconds=(datetime.now() - start_time).total_seconds(),
            )

        if link_info.link_type in ["CHANNEL", "CHANNEL_HANDLE"]:
            return ProcessingResult(
                video_id=link_info.channel_id or "unknown",
                title="Channel",
                status="skipped",
                output_dir=str(self.output_base_dir),
                error_message="Channel detected. Use --process-channel flag to download all videos.",
                processing_time_seconds=(datetime.now() - start_time).total_seconds(),
            )

        video_id = link_info.video_id

        # Step 2: Create output directory for this video
        video_output_dir = self.output_base_dir / video_id
        video_output_dir.mkdir(parents=True, exist_ok=True)

        # Step 3: Extract metadata
        metadata = MetadataExtractor.extract(video_url)
        if not metadata:
            return ProcessingResult(
                video_id=video_id,
                title="Unknown",
                status="error",
                output_dir=str(video_output_dir),
                error_message="Failed to extract metadata",
                processing_time_seconds=(datetime.now() - start_time).total_seconds(),
            )

        # Step 4: Extract audio
        audio_temp_dir = video_output_dir / "audio_temp"
        audio_path = AudioExtractor.extract(video_url, str(audio_temp_dir))
        if not audio_path:
            return ProcessingResult(
                video_id=video_id,
                title=metadata.title,
                status="error",
                metadata=metadata,
                output_dir=str(video_output_dir),
                error_message="Failed to extract audio",
                processing_time_seconds=(datetime.now() - start_time).total_seconds(),
            )

        # Step 5: Transcribe
        transcript_dir = video_output_dir / "whisperx_output"
        transcript_dir.mkdir(parents=True, exist_ok=True)

        entries = TranscriptionEngine.transcribe(
            audio_path=audio_path,
            output_dir=str(transcript_dir),
            language=self.language,
            compute_type=self.compute_type,
            enable_diarization=self.enable_diarization,
            hf_token=self.hf_token,
        )

        if not entries:
            return ProcessingResult(
                video_id=video_id,
                title=metadata.title,
                status="error",
                metadata=metadata,
                output_dir=str(video_output_dir),
                error_message="Transcription failed",
                processing_time_seconds=(datetime.now() - start_time).total_seconds(),
            )

        # Step 6: Save outputs
        transcript_text = " ".join([entry.text for entry in entries])
        markdown_output = OutputFormatter.format_markdown(metadata, entries)
        json_output = OutputFormatter.format_json(metadata, entries)

        # Save Markdown
        markdown_path = video_output_dir / "transcript.md"
        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(markdown_output)

        # Save JSON
        json_path = video_output_dir / "transcript.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json_output)

        # Save metadata
        metadata_path = video_output_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata.dict(), f, indent=2, ensure_ascii=False)

        # Cleanup temporary audio files
        import shutil
        shutil.rmtree(audio_temp_dir, ignore_errors=True)
        shutil.rmtree(transcript_dir, ignore_errors=True)

        return ProcessingResult(
            video_id=video_id,
            title=metadata.title,
            status="success",
            metadata=metadata,
            transcript=entries,
            transcript_text=transcript_text,
            output_dir=str(video_output_dir),
            processing_time_seconds=(datetime.now() - start_time).total_seconds(),
        )
