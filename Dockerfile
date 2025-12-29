# Multi-stage Dockerfile for YouTube Knowledge Base Web App
# Runs FastAPI backend server with embedded web UI

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies (FFmpeg + build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    curl \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip, setuptools, wheel
RUN pip install --upgrade pip setuptools wheel

# Stage 2: Python dependencies layer (improves caching)
FROM base as dependencies

WORKDIR /tmp
COPY backend/requirements.txt .

# Install dependencies with better error handling
RUN pip install --no-cache-dir -r requirements.txt || \
    (echo "Retrying with pip build isolation disabled..." && \
     pip install --no-cache-dir --no-build-isolation -r requirements.txt)

# Stage 3: Final application image
FROM dependencies as final

WORKDIR /app

# Copy backend application code
COPY backend/ ./backend/

# Create necessary directories
RUN mkdir -p /app/transcripts \
    /app/metadata/channels \
    /app/metadata/playlists \
    /app/metadata/videos \
    /app/queue \
    /root/.cache/huggingface

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI server
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
