# 🎥 YouTube Knowledge Base - Development Guide

**Status**: 🚀 Starting Development - M1 (Milestone 1)

---

## 📋 Quick Reference

- **Main Milestone Docs**: See [MILESTONES.md](./MILESTONES.md)
- **Git Workflow**: Test → Commit → Demo
- **Current Milestone**: M1 - Project Structure
- **Next Demo**: FastAPI + React loads on localhost

---

## 🏗️ Project Architecture

```
youtube-knowledge-base/
├── backend/                          # FastAPI backend
│   ├── main.py                      # FastAPI app
│   ├── requirements.txt             # Python dependencies
│   ├── models.py                    # Pydantic models
│   ├── database.py                  # SQLite setup (M2)
│   ├── crud.py                      # Database operations (M2)
│   ├── metadata_store.py            # File storage (M3)
│   ├── youtube_utils.py             # URL detection (M6)
│   ├── youtube_extractor.py         # Extraction logic (M7-M9)
│   ├── worker.py                    # Background worker (M18)
│   ├── logger.py                    # Logging (M20)
│   └── tests/                       # Test suite
│       ├── conftest.py              # Pytest fixtures
│       ├── test_database.py         # M2 tests
│       ├── test_metadata_store.py   # M3 tests
│       └── ...
│
├── frontend/                         # React frontend
│   ├── src/
│   │   ├── components/              # React components
│   │   │   ├── URLInput.tsx         # M4
│   │   │   ├── MetadataTree.tsx     # M10-M13
│   │   │   ├── QueuePanel.tsx       # M15-M17
│   │   │   └── JobCard.tsx          # M16
│   │   ├── hooks/
│   │   │   └── useQueueWebSocket.ts # M19
│   │   ├── api.ts                   # API client
│   │   ├── App.tsx                  # Main layout
│   │   └── App.css                  # Styles
│   ├── package.json
│   └── tsconfig.json
│
├── Dockerfile                        # Multi-stage build
├── docker-compose.yml               # Services orchestration
├── MILESTONES.md                    # 20-milestone roadmap
└── README_DEV.md                    # This file

```

---

## 🚀 Getting Started

### Prerequisites
```bash
# Required
- Docker Desktop (with Docker Compose)
- Node.js 18+
- Python 3.11+
- Git

# Optional
- VS Code with Docker extension
- Python extension for VS Code
```

### Initial Setup

```bash
# 1. Clone repo (already done)
cd /Users/udhaya10/workspace/YoutubeTranscripts

# 2. Install Python dependencies (for local testing)
pip install -r backend/requirements.txt
pip install pytest pytest-cov pytest-asyncio

# 3. Install frontend dependencies (for local testing)
cd frontend && npm install && cd ..

# 4. Run tests locally
pytest backend/tests/ -v

# 5. Build Docker
docker compose build

# 6. Run Docker
docker compose up
```

---

## 🧪 Testing Requirements

**CRITICAL**: All tests must pass before commit!

### Running Tests

```bash
# Run ALL tests
pytest backend/tests/ -v

# Run with coverage
pytest backend/tests/ -v --cov=backend

# Run specific test file
pytest backend/tests/test_database.py -v

# Run specific test
pytest backend/tests/test_database.py::test_create_job -v

# Run tests matching pattern
pytest backend/tests/ -k "database" -v
```

### Test Structure
```
backend/tests/
├── conftest.py          # Fixtures & setup
├── test_database.py     # Database operations (M2)
├── test_metadata_store.py # File storage (M3)
├── test_youtube_utils.py  # URL parsing (M6)
├── test_youtube_extractor.py # Extraction (M7-M9)
├── test_api_endpoints.py  # API endpoints
├── test_worker.py       # Background worker (M18)
└── test_websocket.py    # WebSocket (M19)
```

### Test Coverage Goal
- Target: >80% coverage
- Minimum: >70% coverage

```bash
# View coverage report
pytest backend/tests/ -v --cov=backend --cov-report=html
# Open htmlcov/index.html
```

---

## 🐳 Docker Workflow

### Build Image
```bash
# Full rebuild (no cache)
docker compose build --no-cache

# Incremental build
docker compose build

# View build logs
docker compose build --progress=plain
```

### Run Locally
```bash
# Start all services
docker compose up

# Run in background
docker compose up -d

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Stop services
docker compose down

# Clean up volumes
docker compose down -v
```

### Accessing Services
- Backend API: http://localhost:8000
- FastAPI Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

---

## 📝 Commit Workflow

**For every milestone, follow this workflow:**

```bash
# 1. Code the feature
# 2. Write tests
# 3. RUN TESTS (MUST PASS)
pytest backend/tests/ -v
# If tests fail, fix code, repeat

# 4. BUILD DOCKER (MUST SUCCEED)
docker compose build
# If build fails, fix dependencies, repeat

# 5. TEST DOCKER (MANUAL VERIFICATION)
docker compose up -d
# Test the feature manually
# Check http://localhost:8000 and http://localhost:3000
docker compose down

# 6. COMMIT ONLY IF ALL PASS
git add .
git commit -m "M[N]: [Milestone Title] - [Brief Description]

- Implemented [feature]
- Tests: [number] tests written and passing
- Docker: Builds and runs successfully
- Demo: [what to test/show]"

# 7. View git log
git log --oneline | head -5
```

### Commit Message Format
```
M1: Project structure + FastAPI scaffold - Initialize project architecture

- Created backend with FastAPI server structure
- Created frontend with React scaffold
- Setup docker-compose.yml with both services
- Tests: 2/2 passing (health check, swagger docs)
- Docker: Builds and runs successfully
- Demo: http://localhost:8000/docs loads, http://localhost:3000 loads
```

---

## 🔍 Debugging Tips

### Backend Debug Mode
```bash
# Run FastAPI with hot reload
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Debug
```bash
# Run React dev server
cd frontend && npm run dev
```

### Database Debug
```bash
# View SQLite database
sqlite3 /path/to/queue.db

# List tables
.tables

# Query jobs
SELECT id, status, progress FROM jobs;

# Exit
.exit
```

### Docker Debug
```bash
# Execute command in running container
docker compose exec backend bash
# Now you're inside the container
ls -la
python -c "import main"

# View container logs
docker compose logs backend --tail=100

# Container shell
docker compose exec backend sh
```

---

## 📊 Current Milestone: M1

### What's Being Built
- [ ] FastAPI server with health endpoint
- [ ] React project scaffold
- [ ] docker-compose with both services

### Expected Tests (M1)
```
backend/tests/test_api_endpoints.py
├── test_health_endpoint() - GET /health returns 200
└── test_swagger_docs() - GET /docs returns Swagger UI
```

### Demo Checklist
- [ ] `docker compose up` succeeds
- [ ] http://localhost:8000/docs loads
- [ ] http://localhost:3000 loads
- [ ] No console errors

### What to Test Manually
1. Visit http://localhost:8000/docs
   - Should see Swagger UI
   - Should see GET /health endpoint

2. Visit http://localhost:3000
   - Should see React app loading
   - Should see no console errors

3. Test health endpoint
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"healthy"}
   ```

---

## 📚 Documentation Reference

### Milestone Docs
- [MILESTONES.md](./MILESTONES.md) - Complete 20-milestone roadmap with all specifications

### Technology Docs
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)
- [SQLite Docs](https://www.sqlite.org/docs.html)
- [shadcn/ui](https://ui.shadcn.com/)
- [WebSocket Docs](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

---

## 🛠️ Useful Commands

```bash
# Git
git status                    # Check status
git log --oneline            # View commits
git diff                     # See changes
git add .                    # Stage changes
git commit -m "..."          # Commit

# Docker
docker compose build         # Build image
docker compose up           # Start services
docker compose down         # Stop services
docker compose logs -f      # View logs

# Python
pytest backend/tests/ -v    # Run tests
pip install -r requirements.txt  # Install deps
python -m pytest --cov=backend  # Coverage

# Frontend
npm install                 # Install deps
npm run dev                 # Dev server
npm run build              # Production build
```

---

## ⚠️ Important Rules

### Before EVERY Commit
- [ ] ALL tests passing: `pytest backend/tests/ -v`
- [ ] Docker builds: `docker compose build`
- [ ] Docker runs: `docker compose up -d` then test manually
- [ ] This README updated if needed
- [ ] MILESTONES.md status updated

### Never
- ❌ Commit with failing tests
- ❌ Commit without rebuilding Docker
- ❌ Skip manual testing
- ❌ Push without updating documentation

---

## 🆘 Troubleshooting

### Docker build fails
```bash
# Clean everything and rebuild
docker compose down -v
docker compose build --no-cache
```

### Port already in use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### Tests not found
```bash
# Ensure conftest.py exists
ls backend/tests/conftest.py

# Run from root directory
pwd  # should be /Users/udhaya10/workspace/YoutubeTranscripts
pytest backend/tests/ -v
```

### Git issues
```bash
# Check git status
git status

# View last few commits
git log --oneline -10

# See what changed
git diff HEAD~1
```

---

## 📞 Session Resume Instructions

If this session terminates and needs to resume:

1. **Check milestone status**:
   ```bash
   git log --oneline | head -5
   ```

2. **Check last test results**:
   ```bash
   pytest backend/tests/ -v
   ```

3. **Read MILESTONES.md** for next milestone details

4. **Continue from next milestone**

---

**Last Updated**: 2025-12-29
**Current Status**: Ready for M1
**Next Action**: Start M1 implementation
