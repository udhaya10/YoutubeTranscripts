# Quick Start Guide - Run Setup

## Option 1: Using the Quick Setup Script (Easiest)

### macOS/Linux:
```bash
cd /Users/udhaya10/workspace/YoutubeTranscripts
./quick_setup.sh
```

### Windows:
```bash
cd YoutubeTranscripts
quick_setup.bat
```

The script will:
- ✅ Create virtual environment if needed
- ✅ Activate the venv
- ✅ Run setup.py with automatic Rich installation
- ✅ Show you the setup wizard

---

## Option 2: Manual Setup (If you prefer step-by-step)

### macOS/Linux:
```bash
# 1. Navigate to project
cd /Users/udhaya10/workspace/YoutubeTranscripts

# 2. Create venv (if not exists)
python3 -m venv .venv

# 3. Activate venv
source .venv/bin/activate

# 4. Run setup
python3 setup.py
```

### Windows (Command Prompt):
```bash
# 1. Navigate to project
cd YoutubeTranscripts

# 2. Create venv (if not exists)
python -m venv .venv

# 3. Activate venv
.venv\Scripts\activate.bat

# 4. Run setup
python setup.py
```

### Windows (PowerShell):
```powershell
# 1. Navigate to project
cd YoutubeTranscripts

# 2. Create venv (if not exists)
python -m venv .venv

# 3. Activate venv
.venv\Scripts\Activate.ps1

# 4. Run setup
python setup.py
```

---

## Option 3: Force Specific Setup Mode

```bash
# Docker setup only
python3 setup.py docker

# Local setup only
python3 setup.py local

# Show help
python3 setup.py --help
```

---

## What the Setup Script Does

### First Time Running setup.py:
1. ✅ Auto-installs Rich library (if not already installed)
2. ✅ Detects your platform (macOS/Linux/Windows)
3. ✅ Recommends Docker or Local setup
4. ✅ Guides you through interactive prompts
5. ✅ Creates all necessary files and configurations
6. ✅ Validates everything is working
7. ✅ Shows you usage examples

### Subsequent Times:
- ✅ Much faster (skips installations)
- ✅ Can reconfigure settings
- ✅ Same interactive wizard

---

## Dependencies are Already Synced ✅

The `requirements.txt` file already includes:
- ✅ Rich (for beautiful CLI)
- ✅ Typer (for CLI framework)
- ✅ All ML dependencies (torch, whisperx, etc.)
- ✅ **psutil** (just added for system resource checks)

All are automatically installed when needed.

---

## Troubleshooting

### "Permission denied" on quick_setup.sh
```bash
chmod +x quick_setup.sh
./quick_setup.sh
```

### Python not found
Make sure Python 3.10+ is installed:
```bash
python3 --version    # Should be 3.10+
```

### Virtual environment errors
Delete the old one and create new:
```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python3 setup.py
```

### Rich installation fails
setup.py will fall back to basic output (still works fine):
```bash
python3 setup.py
# Script will auto-install Rich and retry
# If it fails, it uses basic print statements
```

---

## What Happens After Setup?

Once setup.py completes, you'll see:

### Docker Setup:
```bash
# Process videos with:
docker compose run --rm youtube-extractor https://youtu.be/VIDEO_ID
```

### Local Setup:
```bash
# Keep venv activated, then:
python main.py https://youtu.be/VIDEO_ID

# Or activate fresh next time:
source .venv/bin/activate
python main.py URL
```

---

## Environment Files (Kept in Sync)

| File | Updated | Synced | Status |
|------|---------|--------|--------|
| requirements.txt | ✅ Added psutil | ✅ | Current |
| .env.example | ✅ Telemetry config | ✅ | Current |
| setup.py | ✅ Auto-installs Rich | ✅ | Current |
| docker/entrypoint.sh | ✅ Telemetry export | ✅ | Current |

All files are in sync. No manual updates needed!

---

## Next Steps

1. **Run the setup:**
   ```bash
   ./quick_setup.sh          # macOS/Linux
   quick_setup.bat           # Windows
   ```

2. **Follow the prompts** - answer the interactive questions

3. **Wait for completion** - setup will validate everything

4. **Process your first video:**
   ```bash
   # Docker
   docker compose run --rm youtube-extractor https://youtu.be/VIDEO_ID

   # Local
   source .venv/bin/activate
   python main.py https://youtu.be/VIDEO_ID
   ```

5. **Check output:**
   ```bash
   cat transcripts/VIDEO_ID/transcript.md
   ```

Done! 🎉

---

*Generated: December 2025*
*All requirements.txt entries synced ✅*
*Ready to run!*
