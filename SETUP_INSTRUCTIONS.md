# YouTube Knowledge Base Extractor - Setup Instructions

## Overview
A powerful, beautifully-designed CLI tool that extracts metadata, transcripts, and speaker information from YouTube videos. Built with Python, leveraging `yt-dlp` for extraction and `WhisperX` for accurate transcription with speaker diarization.

**Target System:** Mac Studio M2 Ultra (or any Mac with Apple Silicon/Intel)  
**Python Version:** 3.10 or higher  
**Primary Dependencies:** `yt-dlp`, `whisperx`, `rich`, `typer`, `pydantic`

---

## Pre-Installation Requirements

### 1. System Dependencies
Before installing Python packages, ensure you have system-level tools:

```bash
# For Mac (using Homebrew)
brew install ffmpeg
```

FFmpeg is required by both `yt-dlp` and `WhisperX` to process audio files.

### 2. HuggingFace Token (Required for Speaker Diarization)

The Pyannote speaker diarization model requires you to accept a user agreement:

1. Go to: https://huggingface.co/pyannote/speaker-diarization-3.1
2. Click "Agree and access repository"
3. Visit: https://huggingface.co/settings/tokens
4. Create a **Read-only** access token
5. Save this token somewhere safe (you'll need it during setup)

---

## Installation Steps

### Step 1: Clone/Download the Project

```bash
# Create a project directory
mkdir ~/youtube-knowledge-base
cd ~/youtube-knowledge-base

# Copy all Python files into this directory
# (main.py, youtube_extractor.py, requirements.txt, setup_instructions.md)
```

### Step 2: Create Virtual Environment

```bash
# Create a Python virtual environment
python3 -m venv venv

# Activate the environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### Step 3: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

**What gets installed:**
- `yt-dlp` - YouTube metadata & audio extraction
- `whisperx` - Speech-to-text with speaker diarization
- `torch` - Machine learning framework (with Metal/MPS support for Mac)
- `rich` - Beautiful terminal output
- `typer` - CLI framework with automatic help
- `pydantic` - Data validation
- `pydub` - Audio processing utilities

### Step 4: Download WhisperX Model (Optional, but Recommended)

The script will auto-download the Whisper model when first run, but you can pre-download to save time:

```bash
# Activate the environment first
source venv/bin/activate

# Download the large-v3 model
whisperx --model large-v3 --language en --compute_type int8 path/to/dummy.mp3
```

This downloads the model to your cache directory (usually `~/.cache/huggingface/`).

---

## First Run Setup

### Step 1: Start the Application

```bash
# Ensure virtual environment is active
source venv/bin/activate

# Run the main script
python main.py
```

### Step 2: Initial Setup Prompt

On first run, the CLI will prompt you for:
1. **HuggingFace Token** - Paste the token you created earlier
2. **Output Directory** - Where to save transcripts (default: `./transcripts/`)
3. **Processing Preferences** - Language, compute type, etc.

These are saved to `config.json` for future runs.

---

## Usage

### Basic Usage

```bash
# Process a single YouTube video
python main.py https://www.youtube.com/watch?v=VIDEO_ID

# Process multiple videos
python main.py https://youtu.be/VIDEO_ID1 https://youtu.be/VIDEO_ID2

# Process a playlist
python main.py https://www.youtube.com/playlist?list=PLAYLIST_ID

# Process from file
python main.py --from-file urls.txt
```

### Advanced Options

```bash
# Show all options
python main.py --help

# Custom output directory
python main.py VIDEO_URL --output-dir ./my_transcripts

# Disable speaker diarization (faster)
python main.py VIDEO_URL --no-diarize

# Use faster compute type (less accurate, but quicker on CPU)
python main.py VIDEO_URL --compute-type float32
```

---

## Project Structure

```
youtube-knowledge-base/
├── main.py                    # CLI entry point (user-facing)
├── youtube_extractor.py       # Core logic (extraction + transcription)
├── requirements.txt           # Python dependencies
├── config.json               # Auto-generated configuration (created on first run)
├── setup_instructions.md     # This file
├── transcripts/              # Output directory (auto-created)
│   ├── video_id_1/
│   │   ├── metadata.json
│   │   ├── transcript.md
│   │   └── transcript.json
│   └── video_id_2/
│       ├── metadata.json
│       ├── transcript.md
│       └── transcript.json
└── logs/                     # Application logs (auto-created)
    └── extractor_YYYY-MM-DD.log
```

---

## Troubleshooting

### Issue: "ffmpeg not found"
**Solution:**
```bash
# Mac
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows (with Chocolatey)
choco install ffmpeg
```

### Issue: "No module named 'torch'"
**Solution:** Re-install dependencies with verbose output:
```bash
pip install --no-cache-dir torch
```

### Issue: "pyannote token required" or "403 Forbidden"
**Solution:**
1. Confirm you accepted the agreement at https://huggingface.co/pyannote/speaker-diarization-3.1
2. Delete `config.json` and re-run to enter token again
3. Verify token is valid: `echo $HF_TOKEN` (should show your token)

### Issue: Script hangs on first run
**This is normal.** The script is downloading the ~3GB Whisper model. On a 100Mbps connection, this takes ~5-10 minutes. Watch the progress in your terminal.

### Issue: "Out of memory" errors on Mac
**Solution:** The script uses `int8` quantization by default, which keeps memory usage low. If still failing:
```bash
# Force CPU mode (slower but uses less memory)
python main.py VIDEO_URL --device cpu
```

### Issue: Metal/GPU not accelerating on Mac
**Solution:** This is a known PyTorch issue. The script defaults to auto-detection. If GPU doesn't work:
```bash
# Force CPU computation
python main.py VIDEO_URL --device cpu
```

---

## Configuration File (config.json)

The script auto-generates this after first run. You can manually edit it:

```json
{
  "hf_token": "your_huggingface_token_here",
  "output_directory": "./transcripts/",
  "default_language": "en",
  "default_compute_type": "int8",
  "enable_diarization": true,
  "max_workers": 4,
  "log_level": "INFO"
}
```

---

## Performance Notes

### Transcription Speed (M2 Ultra with 64GB RAM)

| Video Length | Compute Type | Approximate Time |
|---|---|---|
| 10 min | int8 (quantized) | ~10-15 seconds |
| 1 hour | int8 (quantized) | ~1-2 minutes |
| 1 hour | float32 (full precision) | ~3-5 minutes |
| 1 hour | CPU only | ~10-20 minutes |

### First Run Setup Time
- Model download: 5-10 minutes (one-time)
- HuggingFace token validation: ~30 seconds
- Total first run: 5-10 minutes

---

## Advanced: Running Multiple Videos Asynchronously

The script automatically queues multiple URLs and processes them sequentially. To process them in the background:

```bash
# Run in background (Mac/Linux)
nohup python main.py urls.txt > output.log 2>&1 &

# Check progress
tail -f output.log

# Get background job ID
jobs
```

Or use a scheduler (see integration guide in project docs).

---

## Integration with n8n (Automation)

For automated extraction workflows:

1. Create an n8n workflow with "Execute Command" node
2. Set command to: `/path/to/venv/bin/python /path/to/main.py "{{youtube_url}}" --output-dir "{{output_folder}}"`
3. Set working directory to project root
4. Parse JSON output for downstream processing

---

## Uninstallation

```bash
# Remove virtual environment
rm -rf venv/

# Remove transcripts and logs (optional)
rm -rf transcripts/ logs/ config.json
```

---

## Support & Contributing

### Reporting Issues
Include:
- Python version: `python --version`
- OS info: `uname -a` (Mac/Linux) or `ver` (Windows)
- Error message: Full terminal output
- Log file: `logs/extractor_*.log`

### Common Questions

**Q: Can I use this on Windows?**  
A: Yes, but some commands differ. Use PowerShell instead of bash. Metal GPU acceleration is Mac-only; Windows will use CPU or NVIDIA CUDA if available.

**Q: How do I process 1000 videos?**  
A: Create a text file with one URL per line, then: `python main.py --from-file my_urls.txt`. The script processes them sequentially. For parallel processing, run multiple instances with `--worker-id 1` and `--total-workers 4`.

**Q: What if I want to use a different model?**  
A: Edit the script's `WHISPER_MODEL` constant or add a `--model` CLI flag (advanced users).

---

## Next Steps

1. Run `python main.py --help` to see all options
2. Process a single test video first: `python main.py https://youtu.be/jNQXAC9IVRw`
3. Check the output in `transcripts/VIDEO_ID/transcript.md`
4. Build your integration (n8n, Zapier, etc.)

---

**Happy extracting! 🚀**

*Last Updated: December 2025*
