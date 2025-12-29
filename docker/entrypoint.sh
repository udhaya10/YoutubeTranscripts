#!/bin/bash
set -e

# Docker entrypoint script for YouTube Transcripts
# Handles initialization and validation before running the main application

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 1. Validate HuggingFace token
if [ -z "$HF_TOKEN" ]; then
    print_error "HF_TOKEN environment variable is not set"
    print_error "Please configure your .env file with HF_TOKEN"
    print_error "Get your token at: https://huggingface.co/settings/tokens"
    exit 1
fi

print_info "HuggingFace token is configured"

# 2. Create output directory if it doesn't exist
OUTPUT_DIR="${OUTPUT_DIR:-/app/transcripts}"
if [ ! -d "$OUTPUT_DIR" ]; then
    print_info "Creating output directory: $OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR"
fi

print_info "Output directory ready: $OUTPUT_DIR"

# 3. Check if config.json exists, create if missing
CONFIG_FILE="/app/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    print_info "Creating initial config.json..."
    cat > "$CONFIG_FILE" <<EOF
{
  "hf_token": "${HF_TOKEN}",
  "output_directory": "${OUTPUT_DIR}",
  "default_language": "${LANGUAGE:-en}",
  "default_compute_type": "${COMPUTE_TYPE:-int8}",
  "enable_diarization": true,
  "max_workers": 4
}
EOF
    print_info "config.json created successfully"
else
    print_info "config.json already exists"
fi

# 4. Verify FFmpeg is available
if ! command -v ffmpeg &> /dev/null; then
    print_error "FFmpeg is not available in the container"
    exit 1
fi

print_info "FFmpeg is available"

# 5. Configure telemetry (default to enabled if not set)
export PYANNOTE_METRICS_ENABLED="${PYANNOTE_METRICS_ENABLED:-1}"
if [ "$PYANNOTE_METRICS_ENABLED" = "0" ]; then
    print_info "PyAnnote telemetry disabled"
else
    print_info "PyAnnote telemetry enabled"
fi

# 6. Verify Python and main script
if [ ! -f "/app/main.py" ]; then
    print_error "main.py not found in /app"
    exit 1
fi

print_info "Application ready to start"

# 6. Execute the main application with all passed arguments
print_info "Starting YouTube Transcripts..."
print_info "Command: python main.py $@"
exec python main.py "$@"
