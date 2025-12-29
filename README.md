# 🎥 YouTube Knowledge Base Extractor

A production-ready Python CLI tool for extracting transcripts, metadata, and speaker information from YouTube videos with speaker diarization. Built for accuracy over speed with a beautiful, user-friendly terminal interface.

**Perfect for:** Building local knowledge bases, research, content analysis, and LLM training datasets.

## Features

✨ **Core Capabilities**
- 🔗 **Intelligent Link Detection** - Recognizes videos, playlists, and channels
- 📊 **Metadata Extraction** - Title, duration, views, upload date, channel info
- 🎙️ **Speaker Diarization** - Identifies "Speaker A", "Speaker B" in conversations
- ⏱️ **Word-Level Timestamps** - Precise timing for every word
- 📝 **Multiple Output Formats** - Markdown (human-readable) + JSON (machine-readable)
- 🚀 **Async Processing** - Handle multiple URLs efficiently
- 💾 **Auto Model Download** - WhisperX model auto-downloads on first run
- 🖥️ **Beautiful CLI** - Rich terminal UI with colors, progress bars, and tables

## System Requirements

- **OS:** macOS (Apple Silicon M1/M2/M3) or any Linux/Windows with Python 3.10+
- **RAM:** 8GB minimum, 16GB+ recommended for smooth transcription
- **Disk:** ~5GB for WhisperX model cache
- **Internet:** For initial model download and YouTube access

## Quick Start ⚡ (Automated Setup)

The easiest way to get started - one command handles everything:

### Docker Setup (Recommended - 5 minutes)

```bash
# 1. Clone the repository
git clone <repo-url>
cd YoutubeTranscripts

# 2. Run automated setup
python setup.py

# Follow the prompts:
# - Choose Docker or local setup
# - Paste your HuggingFace token (optional, for speaker identification)
# - Wait for setup to complete

# 3. Process your first video
docker compose run --rm youtube-extractor https://youtu.be/VIDEO_ID

# 4. Find output in ./transcripts/
```

**What the setup script does automatically:**
- ✓ Detects your OS and recommends Docker or local setup
- ✓ Checks Docker installation (for Docker setup)
- ✓ Prompts for HuggingFace token with instructions
- ✓ Builds Docker image with FFmpeg + all dependencies
- ✓ Validates everything before finishing
- ✓ Shows usage examples

### Local Setup (Alternative - 5-10 minutes)

```bash
# 1. Clone the repository
git clone <repo-url>
cd YoutubeTranscripts

# 2. Run automated setup (local mode)
python setup.py local

# Follow the prompts:
# - Auto-installs FFmpeg (brew/apt/choco based on OS)
# - Creates Python virtual environment
# - Installs all dependencies
# - Asks for HuggingFace token
# - Validates installation

# 3. Activate virtual environment and process videos
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

python main.py https://youtu.be/VIDEO_ID
```

---

## Manual Installation (Optional - For Advanced Users)

If you prefer to set up manually or the automated setup doesn't work:

### 1. Prerequisites

```bash
# Install FFmpeg (required)
brew install ffmpeg  # macOS
# OR
sudo apt-get install ffmpeg  # Ubuntu/Debian
# OR
choco install ffmpeg  # Windows (with Chocolatey)
```

### 2. Clone and Setup

```bash
# Create project directory
mkdir ~/youtube-knowledge-base
cd ~/youtube-knowledge-base

# Clone this repository (or download files)
git clone <repo-url> .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Get HuggingFace Token (for speaker diarization)

1. Visit: https://huggingface.co/pyannote/speaker-diarization-3.1
2. Click "Agree and access repository"
3. Create a read token at: https://huggingface.co/settings/tokens
4. Save your token (you'll need it in the next step)

### 4. First Run Setup

```bash
python main.py setup
# OR just run any command and you'll be prompted:
python main.py https://youtu.be/dQw4w9WgXcQ
```

You'll be asked to:
- Paste your HuggingFace token
- Choose output directory
- Select transcription language
- Pick compute type (int8 for faster, float32 for more accurate)

## Usage

### Basic: Single Video

```bash
python main.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

### Multiple Videos

```bash
python main.py \
  https://youtu.be/VIDEO_ID1 \
  https://youtu.be/VIDEO_ID2 \
  https://youtu.be/VIDEO_ID3
```

### From a File

Create `urls.txt`:
```
https://youtu.be/VIDEO_ID1
https://youtu.be/VIDEO_ID2
https://youtu.be/VIDEO_ID3
```

Then:
```bash
python main.py --from-file urls.txt
```

### Advanced Options

```bash
# Custom output directory
python main.py VIDEO_URL --output-dir /path/to/output

# Disable speaker diarization (faster)
python main.py VIDEO_URL --no-diarize

# Use faster compute type (less accurate)
python main.py VIDEO_URL --compute-type float32

# Change language
python main.py VIDEO_URL --language es  # Spanish

# Force CPU computation (for troubleshooting)
python main.py VIDEO_URL --device cpu

# View all options
python main.py --help
```

## Output Structure

```
transcripts/
├── VIDEO_ID_1/
│   ├── metadata.json          # Video metadata
│   ├── transcript.md          # Human-readable transcript with speakers
│   └── transcript.json        # Machine-readable full transcript
├── VIDEO_ID_2/
│   ├── metadata.json
│   ├── transcript.md
│   └── transcript.json
└── VIDEO_ID_3/
    └── ...
```

### Example Markdown Output

```markdown
# My Amazing Video Title

**Channel:** John Doe  
**Video ID:** dQw4w9WgXcQ  
**Duration:** 45 minutes  
**Views:** 1,234,567  
**Uploaded:** 2024-01-15  

---

## Transcript

**Speaker 1:**

[00:00] Welcome to the show today we're going to talk about...
[00:15] This is really important because...

**Speaker 2:**

[01:30] I totally agree with that point...
[02:00] Let me add something to that...
```

### Example JSON Output

```json
{
  "metadata": {
    "video_id": "dQw4w9WgXcQ",
    "title": "My Amazing Video",
    "channel": "John Doe",
    "duration_seconds": 2700,
    "view_count": 1234567,
    ...
  },
  "transcript": [
    {
      "start": 0.0,
      "end": 15.5,
      "text": "Welcome to the show today we're going to talk about...",
      "speaker": "Speaker 1"
    },
    {
      "start": 15.5,
      "end": 30.2,
      "text": "This is really important because...",
      "speaker": "Speaker 1"
    },
    ...
  ],
  "generated_at": "2024-01-20T14:30:45.123456"
}
```

## Configuration

After first run, edit `config.json` to customize defaults:

```json
{
  "hf_token": "your_huggingface_token_here",
  "output_directory": "./transcripts/",
  "default_language": "en",
  "default_compute_type": "int8",
  "enable_diarization": true,
  "max_workers": 4
}
```

## GPU Acceleration (Optional)

For **2-3x faster transcription** with NVIDIA GPUs:

### Prerequisites
- NVIDIA GPU (GTX 1060+)
- CUDA 12.8 installed
- cuDNN libraries

### Installation

**For Linux:**
1. Install CUDA 12.8: https://docs.nvidia.com/cuda/cuda-installation-guide-linux/
2. Reinstall PyTorch with CUDA support:
```bash
pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```

**For Windows:**
1. Download CUDA 12.8: https://developer.nvidia.com/cuda-12-8-1-download-archive
2. Run installer and follow prompts
3. Reinstall PyTorch:
```bash
pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```

**For macOS:**
GPU acceleration not available (uses Metal for Apple Silicon automatically)

### Usage

After CUDA installation, run with:
```bash
# Local setup
python main.py "https://youtu.be/VIDEO_ID" --device cuda

# Docker (requires nvidia-docker)
docker run --gpus all youtube-transcripts https://youtu.be/VIDEO_ID --device cuda
```

### Verify GPU is Working
```bash
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

## Performance (M2 Ultra)

| Video Length | Device | Compute Type | Time |
|---|---|---|---|
| 10 min | M2 GPU | int8 | ~5-8s |
| 1 hour | M2 GPU | int8 | ~45-60s |
| 1 hour | NVIDIA GPU | int8 | ~30-45s |
| 1 hour | CPU | int8 | ~10-20 min |

*First run includes ~5-10 min for model download*

## Performance (M2 Ultra - Legacy)

| Video Length | Compute Type | Time |
|---|---|---|
| 10 min | int8 | ~10-15s |
| 1 hour | int8 | ~1-2 min |
| 1 hour | float32 | ~3-5 min |
| 1 hour | CPU only | ~10-20 min |

*First run includes ~5-10 min for model download*

## Troubleshooting

### "ffmpeg not found"
```bash
brew install ffmpeg
```

### "No module named 'torch'"
```bash
pip install --no-cache-dir torch
```

### "pyannote token required"
1. Accept agreement at https://huggingface.co/pyannote/speaker-diarization-3.1
2. Delete `config.json`
3. Re-run to re-enter token

### Model hangs on download
This is normal. The ~3GB model is downloading. Monitor your internet. On 100Mbps, expect 5-10 minutes.

### Out of memory errors
```bash
# Use CPU instead of GPU
python main.py URL --device cpu

# Or reduce compute precision
python main.py URL --compute-type float32
```

### Metal/GPU not accelerating on Mac
This is a PyTorch issue. The script auto-detects. If GPU doesn't work:
```bash
python main.py URL --device cpu
```

### GPU Running Slowly on NVIDIA
1. Verify GPU is detected:
```bash
python -c "import torch; print(torch.cuda.is_available())"
```
2. Check CUDA version matches PyTorch (12.8):
```bash
nvcc --version
```
3. Reinstall PyTorch with correct CUDA:
```bash
pip install --upgrade torch --index-url https://download.pytorch.org/whl/cu128
```

## Privacy & Telemetry

**PyAnnote Usage Data:**
- PyAnnote (speaker diarization) collects optional anonymous telemetry
- This includes: model name, device type, processing time (no audio/text content)
- Telemetry is **enabled by default** but can be disabled

**Disable telemetry:**

For Docker:
```bash
# Edit .env
PYANNOTE_METRICS_ENABLED=0
docker compose up
```

For Local:
```bash
# Set environment variable
export PYANNOTE_METRICS_ENABLED=0
python main.py URL
```

**Data Storage:**
- Transcripts: Stored locally in `./transcripts/` directory
- Config: Stored locally in `config.json` (contains HF token, **never commit**)
- No data is sent to cloud services (except YouTube for video/audio download)

## Integration Examples

### With n8n (Automation)

Create an n8n workflow:
1. Use "Execute Command" node
2. Command: `/path/to/venv/bin/python /path/to/main.py "{{youtube_url}}"`
3. Parse JSON output for downstream processing

### Batch Processing in Background

```bash
# Run 100 videos in background
nohup python main.py --from-file urls.txt > processing.log 2>&1 &

# Monitor progress
tail -f processing.log

# Check if still running
jobs
```

### With Local LLM (Next Phase)

```python
# Load transcripts for vector embedding
import json
from pathlib import Path

for transcript_file in Path("transcripts").glob("*/transcript.json"):
    with open(transcript_file) as f:
        data = json.load(f)
        # Send to embedding model
        # Store in vector database
        # Build semantic search
```

## Architecture

```
YouTube URL
    ↓
[Link Detection] → Regex parsing, type identification
    ↓
[Metadata Extraction] → yt-dlp (title, views, duration, etc.)
    ↓
[Audio Extraction] → Download MP3 from video
    ↓
[Transcription] → WhisperX (large-v3 model)
    ↓
[Word Alignment] → Precise timestamps
    ↓
[Diarization] → Speaker identification (PyAnnote)
    ↓
[Output Formatting] → Markdown + JSON
    ↓
Local Files (Ready for LLM)
```

## Advanced: Custom Model Configuration

To use a different Whisper model:

```python
# Edit youtube_extractor.py, line ~400
# Change:
"--model", "large-v3",
# To:
"--model", "medium",  # Faster but less accurate
"--model", "base",    # Much faster, lower quality
```

Available models: `tiny`, `base`, `small`, `medium`, `large`, `large-v3`

## Project Structure

```
youtube-knowledge-base/
├── main.py                 # CLI entry point
├── youtube_extractor.py    # Core extraction logic
├── requirements.txt        # Python dependencies
├── SETUP_INSTRUCTIONS.md   # Detailed setup guide
├── README.md              # This file
├── config.json            # Auto-generated config
├── transcripts/           # Output directory
│   ├── VIDEO_ID_1/
│   ├── VIDEO_ID_2/
│   └── ...
└── logs/                  # Application logs
```

## Development

### Run Tests

```bash
# Coming soon: pytest test_*.py
```

### Contributing

Contributions welcome! Areas for improvement:
- [ ] Batch playlist processing
- [ ] Parallel video downloading
- [ ] WebUI interface
- [ ] API server mode
- [ ] Cloud storage integration

## License

MIT License - See LICENSE file

## Support

- **Issues:** Check GitHub issues or create a new one
- **Questions:** Open a discussion
- **Feature Requests:** Create an enhancement issue

## Performance Tips

1. **M2 Ultra:** Use `int8` (quantized) mode for speed
2. **Limited RAM:** Use `--compute-type float32` with CPU
3. **High Accuracy:** Use `float32` compute type (slower)
4. **Multiple Videos:** Use `--from-file` for better batching

## What's Next?

Phase 2 (Coming Soon):
- Vector embedding with Sentence-Transformers
- Local vector database (FAISS/Weaviate)
- Semantic search across all transcripts
- Integration with local LLMs (Ollama + Mistral)
- RAG (Retrieval-Augmented Generation) pipeline

---

**Built with ❤️ for accurate, privacy-first YouTube knowledge extraction**

*Last updated: December 2025*
