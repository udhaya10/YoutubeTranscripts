#!/bin/bash

# YouTube Transcripts - Quick Setup Script
# This script activates the virtual environment and runs setup.py

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   YouTube Transcripts - Quick Setup                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Virtual environment not found. Creating it..."
    python3 -m venv "$VENV_DIR"
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate venv
echo "🔄 Activating virtual environment..."
source "$VENV_DIR/bin/activate"
echo "✅ Virtual environment activated"
echo ""

# Check if setup.py exists
if [ ! -f "$PROJECT_DIR/setup.py" ]; then
    echo "❌ Error: setup.py not found in $PROJECT_DIR"
    exit 1
fi

# Run setup.py
echo "🚀 Running setup.py..."
echo ""
python3 "$PROJECT_DIR/setup.py" "$@"

echo ""
echo "✅ Setup complete!"
