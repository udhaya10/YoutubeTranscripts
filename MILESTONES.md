# 🎯 YouTube Knowledge Base - 20 Milestones Roadmap

**Project**: YouTube Transcripts with Queue System & Real-time Processing
**Status**: Starting M1
**Last Updated**: 2025-12-29

---

## 📋 MILESTONE OVERVIEW

| # | Milestone | Phase | Status | Est. Time | Demo Expected |
|---|-----------|-------|--------|-----------|----------------|
| 1 | Project structure + FastAPI scaffold | Foundation | ⏳ | 1h | FastAPI + React loads |
| 2 | SQLite queue schema + CRUD | Foundation | ⏳ | 1.5h | Can create/read jobs |
| 3 | File-based metadata storage | Foundation | ⏳ | 1h | Files saved to disk |
| 4 | React UI scaffold | Foundation | ⏳ | 1.5h | Empty components render |
| 5 | Docker compose setup | Foundation | ⏳ | 1h | Everything runs together |
| 6 | YouTube URL detection | Data Layer | ⏳ | 1h | Regex detects URL types |
| 7 | Single video extraction | Data Layer | ⏳ | 1.5h | Extract 1 video metadata |
| 8 | Playlist extraction | Data Layer | ⏳ | 1.5h | Extract playlist with videos |
| 9 | Channel extraction | Data Layer | ⏳ | 1.5h | Extract all playlists |
| 10 | Basic tree component | Tree UI | ⏳ | 1.5h | Tree renders (hardcoded) |
| 11 | Tree displays real data | Tree UI | ⏳ | 1.5h | Tree loads from API |
| 12 | Add playlist checkboxes | Tree UI | ⏳ | 1h | Check playlists |
| 13 | Add video checkboxes | Tree UI | ⏳ | 1h | Check individual videos |
| 14 | Add to queue endpoint | Queue | ⏳ | 1.5h | Videos queued in DB |
| 15 | Queue display (list) | Queue | ⏳ | 1.5h | Show pending jobs |
| 16 | Queue display (cards) | Queue | ⏳ | 1.5h | Cards instead of list |
| 17 | Progress bars on cards | Queue | ⏳ | 1h | Visual progress |
| 18 | Background job worker | Processing | ⏳ | 2h | Videos transcribe |
| 19 | WebSocket real-time | Processing | ⏳ | 1.5h | Live progress updates |
| 20 | Error handling + recovery | Polish | ⏳ | 1.5h | Resilient system |

---

## 🔧 DETAILED MILESTONE SPECIFICATIONS

### **PHASE 1: FOUNDATION (M1-M5)**

#### **M1: Project Structure + FastAPI Server Scaffold** ⏳
**Status**: Not started
**Est. Time**: 1 hour
**Goals**:
- [ ] Create backend structure with FastAPI
- [ ] Create frontend structure with React
- [ ] Create Dockerfile with both services
- [ ] Update docker-compose.yml

**Deliverables**:
```
backend/
  ├── main.py (FastAPI app)
  ├── requirements.txt
  └── models.py

frontend/
  ├── src/App.tsx
  ├── package.json
  └── tsconfig.json

├── Dockerfile
├── docker-compose.yml
└── .dockerignore
```

**Tests to Write**:
- [ ] FastAPI health check endpoint: `GET /health`
- [ ] FastAPI Swagger docs load: `GET /docs`

**Acceptance Criteria**:
- FastAPI starts on port 8000
- React dev server runs on port 3000
- Both services accessible in browser
- No console errors

**Demo**:
- Show http://localhost:8000/docs
- Show http://localhost:3000

**Commit Message**: `M1: Initialize project structure with FastAPI and React scaffold`

---

#### **M2: SQLite Queue Schema + CRUD Operations** ⏳
**Status**: Not started
**Est. Time**: 1.5 hours
**Goals**:
- [ ] Create SQLite database with jobs table
- [ ] Implement CRUD operations
- [ ] Create Pydantic models for job

**Deliverables**:
```
backend/
  ├── database.py (SQLite setup)
  ├── models.py (Job Pydantic model)
  ├── crud.py (Create, Read, Update operations)
  └── schemas.py (API schemas)
```

**Database Schema**:
```sql
CREATE TABLE jobs (
  id TEXT PRIMARY KEY,
  video_id TEXT NOT NULL,
  video_title TEXT,
  playlist_id TEXT,
  channel_id TEXT,
  status TEXT DEFAULT 'pending', -- pending, processing, completed, failed
  progress FLOAT DEFAULT 0.0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  error_message TEXT,
  retry_count INTEGER DEFAULT 0,
  output_paths TEXT, -- JSON: {transcript_md, transcript_json, metadata}
  metadata JSONB -- Extra data
);
```

**Tests to Write**:
- [ ] `test_create_job()` - Create job, verify in DB
- [ ] `test_read_job()` - Read job by ID
- [ ] `test_update_job_status()` - Update status to processing
- [ ] `test_list_pending_jobs()` - Query all pending jobs
- [ ] `test_job_persistence()` - Data survives restarts

**Acceptance Criteria**:
- Jobs table created
- Can create, read, update jobs
- Database file persists in volume

**Demo**:
- Show database file: `/app/queue.db`
- Python script creates and retrieves job
- Show database contents

**Commit Message**: `M2: Implement SQLite queue schema and CRUD operations`

---

#### **M3: File-Based Metadata Storage System** ⏳
**Status**: Not started
**Est. Time**: 1 hour
**Goals**:
- [ ] Create metadata storage layer
- [ ] Save metadata to JSON
- [ ] Save metadata to Markdown
- [ ] Load metadata back

**Deliverables**:
```
backend/
  └── metadata_store.py

Directory Structure:
/app/metadata/
  ├── channels/
  ├── playlists/
  └── videos/
```

**Metadata File Examples**:
```
channels/channel_UCuAXFkgsw1L7xaCfnd5JJOw.json
playlists/playlist_PLxxxxx.json
videos/video_dQw4w9WgXcQ.json
```

**Tests to Write**:
- [ ] `test_save_channel_metadata()` - Save channel, file created
- [ ] `test_save_playlist_metadata()` - Save playlist, file created
- [ ] `test_save_video_metadata()` - Save video, file created
- [ ] `test_load_metadata()` - Load and verify structure
- [ ] `test_markdown_generation()` - Markdown file created with content

**Acceptance Criteria**:
- Metadata files created in correct directories
- JSON and Markdown files both exist
- Data structure is correct
- Can load metadata back

**Demo**:
- Show directory structure
- Show example JSON and Markdown files

**Commit Message**: `M3: Implement file-based metadata storage system`

---

#### **M4: React UI Scaffold + Basic Components** ⏳
**Status**: Not started
**Est. Time**: 1.5 hours
**Goals**:
- [ ] Create React components structure
- [ ] Setup shadcn/ui
- [ ] Create layout components
- [ ] Setup Tailwind CSS

**Deliverables**:
```
frontend/src/
  ├── components/
  │   ├── URLInput.tsx
  │   ├── MetadataTree.tsx
  │   ├── QueuePanel.tsx
  │   ├── JobCard.tsx
  │   └── Header.tsx
  ├── api.ts (API client)
  ├── hooks/useQueueWebSocket.ts
  ├── App.tsx (main layout)
  └── App.css
```

**Tests to Write**:
- [ ] Component snapshot tests (React Testing Library)
- [ ] `test_url_input_component_renders()`
- [ ] `test_metadata_tree_component_renders()`

**Acceptance Criteria**:
- React loads without errors
- Components render (empty)
- No TypeScript errors
- Tailwind CSS loads

**Demo**:
- Show UI in browser
- Show no console errors

**Commit Message**: `M4: Create React UI scaffold with shadcn/ui components`

---

#### **M5: Docker Compose Setup** ⏳
**Status**: Not started
**Est. Time**: 1 hour
**Goals**:
- [ ] Configure docker-compose with all services
- [ ] Setup volume mounts
- [ ] Setup environment variables
- [ ] Test full stack

**Deliverables**:
```yaml
services:
  backend:
    build: .
    ports: ["8000:8000"]
    volumes:
      - ./backend:/app/backend
      - ./transcripts:/app/transcripts
      - ./metadata:/app/metadata
      - ./queue:/app/queue

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    volumes:
      - ./frontend:/app/frontend

volumes:
  whisper-cache:
```

**Tests to Write**:
- [ ] `test_docker_build_succeeds()` - Docker image builds
- [ ] `test_services_start()` - All services start
- [ ] `test_volume_mounts_work()` - Files persist

**Acceptance Criteria**:
- `docker compose up` works
- Backend accessible on 8000
- Frontend accessible on 3000
- Volumes mount correctly

**Demo**:
- Run `docker compose up`
- Show services starting
- Access both services

**Commit Message**: `M5: Setup Docker Compose with all services and volumes`

---

### **PHASE 2: DATA LAYER (M6-M9)**

#### **M6: YouTube URL Detection (Regex-based)** ⏳
**Status**: Not started
**Est. Time**: 1 hour
**Goals**:
- [ ] Create URL parser with regex
- [ ] Detect video vs playlist vs channel
- [ ] Extract IDs from URLs

**Deliverables**:
```
backend/
  └── youtube_utils.py
      └── YouTubeURLParser class
```

**Tests to Write**:
- [ ] `test_detect_single_video_url()`
- [ ] `test_detect_playlist_url()`
- [ ] `test_detect_channel_url()`
- [ ] `test_detect_invalid_url()`
- [ ] `test_extract_video_ids()` - from various URL formats
- [ ] `test_extract_playlist_id()`
- [ ] `test_extract_channel_id()`

**Acceptance Criteria**:
- All URL formats detected correctly
- IDs extracted correctly
- Invalid URLs return unknown

**Demo**:
- Run Python script with test URLs
- Show detection results

**Commit Message**: `M6: Implement YouTube URL detection with regex parser`

---

#### **M7: Single Video Extraction + JSON Save** ⏳
**Status**: Not started
**Est. Time**: 1.5 hours
**Goals**:
- [ ] Use yt-dlp to extract video metadata
- [ ] Save as JSON and Markdown
- [ ] Create API endpoint
- [ ] Setup error handling

**Deliverables**:
```
backend/main.py
  POST /api/extract/video

backend/youtube_extractor.py
  extract_single_video(video_id)
```

**Tests to Write**:
- [ ] `test_extract_video_metadata()` - Get video info
- [ ] `test_save_video_json()` - Save to JSON
- [ ] `test_save_video_markdown()` - Save to Markdown
- [ ] `test_extract_video_api_endpoint()` - POST endpoint works
- [ ] `test_extract_video_with_invalid_url()` - Error handling

**Acceptance Criteria**:
- Video metadata extracted
- Files saved to `/app/metadata/videos/`
- API endpoint works
- Error handling in place

**Demo**:
- Call API with video URL
- Show extracted JSON and Markdown files

**Commit Message**: `M7: Implement single video extraction with yt-dlp`

---

#### **M8: Playlist Extraction + Video List + JSON** ⏳
**Status**: Not started
**Est. Time**: 1.5 hours
**Goals**:
- [ ] Extract all videos from playlist
- [ ] Get video count
- [ ] Save complete structure
- [ ] Create API endpoint

**Deliverables**:
```
backend/main.py
  POST /api/extract/playlist

backend/youtube_extractor.py
  extract_playlist(playlist_id)
```

**Tests to Write**:
- [ ] `test_extract_playlist_videos()` - Get all videos
- [ ] `test_extract_playlist_metadata()` - Get title, etc.
- [ ] `test_save_playlist_structure()` - Save with nested videos
- [ ] `test_extract_playlist_api_endpoint()` - POST endpoint
- [ ] `test_handle_empty_playlist()` - Edge case

**Acceptance Criteria**:
- All videos extracted from playlist
- Video count correct
- Files saved with correct structure
- API works

**Demo**:
- Extract a playlist
- Show file structure with all videos

**Commit Message**: `M8: Implement playlist extraction with video enumeration`

---

#### **M9: Channel Extraction + All Playlists** ⏳
**Status**: Not started
**Est. Time**: 1.5 hours
**Goals**:
- [ ] Extract all playlists from channel
- [ ] Get video count for each
- [ ] Save complete structure
- [ ] Create API endpoint

**Deliverables**:
```
backend/main.py
  POST /api/extract/channel

backend/youtube_extractor.py
  extract_channel(channel_id)
```

**Tests to Write**:
- [ ] `test_extract_channel_playlists()` - Get all playlists
- [ ] `test_get_playlist_video_counts()` - Count videos per playlist
- [ ] `test_save_channel_structure()` - Save complete tree
- [ ] `test_extract_channel_api_endpoint()` - POST endpoint
- [ ] `test_handle_channel_with_no_playlists()` - Edge case

**Acceptance Criteria**:
- All playlists extracted
- Video counts accurate
- Tree structure saved
- API works

**Demo**:
- Extract a channel
- Show all playlists with video counts

**Commit Message**: `M9: Implement channel extraction with playlist hierarchy`

---

### **PHASE 3: TREE UI (M10-M13)**

#### **M10: Basic Tree Component (React)** ⏳
**Status**: Not started
**Est. Time**: 1.5 hours
**Goals**:
- [ ] Create recursive tree component
- [ ] Support expand/collapse
- [ ] Show hierarchy visually
- [ ] Hardcoded data for testing

**Deliverables**:
```
frontend/src/
  └── components/MetadataTree.tsx
```

**Tests to Write**:
- [ ] Component snapshot tests
- [ ] `test_tree_renders_with_hardcoded_data()`
- [ ] `test_tree_expand_collapse_toggles()`
- [ ] `test_tree_shows_correct_hierarchy()`

**Acceptance Criteria**:
- Tree renders without errors
- Can expand/collapse nodes
- Hierarchy visually clear

**Demo**:
- Show tree in UI
- Expand/collapse nodes

**Commit Message**: `M10: Create recursive tree component with expand/collapse`

---

#### **M11: Tree Displays Channel → Playlists → Videos** ⏳
**Status**: Not started
**Est. Time**: 1.5 hours
**Goals**:
- [ ] Fetch real metadata from API
- [ ] Display in tree component
- [ ] Load data on mount
- [ ] Handle loading state

**Deliverables**:
```
frontend/src/
  ├── components/MetadataTree.tsx (updated)
  ├── api.ts (add fetchChannelMetadata)
  └── App.tsx (add state management)

backend/main.py
  GET /api/metadata/channel/{channel_id}
```

**Tests to Write**:
- [ ] `test_fetch_channel_metadata_api()` - API returns data
- [ ] `test_tree_renders_with_api_data()` - Tree displays
- [ ] `test_loading_state_shows()` - Loading indicator
- [ ] `test_tree_updates_when_data_changes()` - State updates

**Acceptance Criteria**:
- Real data displayed in tree
- Loading state shown
- Tree structure correct: Channel → Playlists → Videos

**Demo**:
- Input channel URL
- API fetches data
- Tree displays in UI

**Commit Message**: `M11: Integrate real metadata API with tree component`

---

#### **M12: Add Checkboxes to Tree (Playlist Level)** ⏳
**Status**: Not started
**Est. Time**: 1 hour
**Goals**:
- [ ] Add checkbox next to each playlist
- [ ] Track selected state
- [ ] Show count of selected playlists

**Deliverables**:
```
frontend/src/
  ├── components/MetadataTree.tsx (updated)
  └── App.tsx (state: selectedPlaylists)
```

**Tests to Write**:
- [ ] `test_playlist_checkbox_toggle()`
- [ ] `test_selected_playlists_state_updates()`
- [ ] `test_count_selected_playlists()` - Display count

**Acceptance Criteria**:
- Checkboxes work
- State tracked correctly
- Count displayed

**Demo**:
- Click checkboxes
- Show selected count

**Commit Message**: `M12: Add checkbox selection for playlists`

---

#### **M13: Add Checkboxes to Individual Videos** ⏳
**Status**: Not started
**Est. Time**: 1 hour
**Goals**:
- [ ] Add checkbox to each video
- [ ] Track selected videos
- [ ] Show total selected count
- [ ] Selecting playlist selects all videos under it

**Deliverables**:
```
frontend/src/
  ├── components/MetadataTree.tsx (updated)
  └── App.tsx (state: selectedVideos)
```

**Tests to Write**:
- [ ] `test_video_checkbox_toggle()`
- [ ] `test_select_playlist_selects_all_videos()`
- [ ] `test_unselect_playlist_unselects_all_videos()`
- [ ] `test_count_total_selected_videos()` - Display count

**Acceptance Criteria**:
- Video checkboxes work
- Playlist selection cascades to videos
- Total count accurate

**Demo**:
- Select playlists and videos
- Show total count

**Commit Message**: `M13: Add checkbox selection for individual videos with cascade`

---

### **PHASE 4: QUEUE SYSTEM (M14-M17)**

#### **M14: 'Add Selected to Queue' Button + API Endpoint** ⏳
**Status**: Not started
**Est. Time**: 1.5 hours
**Goals**:
- [ ] Create "Add to Queue" button
- [ ] Collect selected video IDs
- [ ] Create API endpoint to add jobs
- [ ] Save jobs to SQLite

**Deliverables**:
```
frontend/src/
  └── App.tsx (add button)

backend/main.py
  POST /api/queue/add-videos
  Input: {video_ids: [...]}
  Output: {queued: N, job_ids: [...]}
```

**Tests to Write**:
- [ ] `test_add_videos_to_queue_endpoint()` - Creates jobs
- [ ] `test_jobs_saved_to_database()` - Verify in DB
- [ ] `test_return_job_ids()` - Response includes IDs
- [ ] `test_empty_selection_handled()` - Edge case
- [ ] `test_duplicate_videos_handled()` - Don't add twice

**Acceptance Criteria**:
- Jobs created in DB
- API returns job IDs
- Jobs have correct status: PENDING

**Demo**:
- Select videos
- Click "Add to Queue"
- Show jobs in database
- Verify count

**Commit Message**: `M14: Implement add-to-queue functionality with API`

---

#### **M15: Queue Display as Simple List in UI** ⏳
**Status**: Not started
**Est. Time**: 1.5 hours
**Goals**:
- [ ] Fetch queue jobs from API
- [ ] Display as list
- [ ] Show job info: title, status
- [ ] Auto-refresh or use WebSocket

**Deliverables**:
```
frontend/src/
  ├── components/QueuePanel.tsx (NEW)
  ├── api.ts (add fetchQueueJobs)
  └── App.tsx (add QueuePanel)

backend/main.py
  GET /api/queue/jobs?status=pending
```

**Tests to Write**:
- [ ] `test_fetch_queue_jobs_api()` - Gets jobs from DB
- [ ] `test_queue_panel_renders_jobs()` - List shows
- [ ] `test_queue_updates_when_new_job_added()` - Refresh
- [ ] `test_empty_queue_handled()` - Show empty state

**Acceptance Criteria**:
- Queue list displays
- Shows correct job count
- Job info visible

**Demo**:
- Add videos to queue
- See list in UI

**Commit Message**: `M15: Implement queue display panel with job list`

---

#### **M16: Convert Queue List to Card View** ⏳
**Status**: Not started
**Est. Time**: 1.5 hours
**Goals**:
- [ ] Create JobCard component
- [ ] Display each job as card
- [ ] Show video thumbnail
- [ ] Show status badge

**Deliverables**:
```
frontend/src/
  ├── components/JobCard.tsx (NEW)
  └── components/QueuePanel.tsx (refactor to use cards)
```

**Tests to Write**:
- [ ] `test_job_card_renders()` - Component renders
- [ ] `test_job_card_shows_title()` - Title displayed
- [ ] `test_job_card_shows_status()` - Status badge
- [ ] `test_multiple_cards_grid_layout()` - Grid display

**Acceptance Criteria**:
- Cards display correctly
- Grid layout responsive
- All info visible

**Demo**:
- Show queue as cards grid

**Commit Message**: `M16: Convert queue display to card component layout`

---

#### **M17: Add Progress Bars to Queue Cards** ⏳
**Status**: Not started
**Est. Time**: 1 hour
**Goals**:
- [ ] Add progress bar to each card
- [ ] Display percentage
- [ ] Update when progress changes
- [ ] Show visual feedback

**Deliverables**:
```
frontend/src/
  └── components/JobCard.tsx (updated)
```

**Tests to Write**:
- [ ] `test_progress_bar_renders()` - Component shows
- [ ] `test_progress_bar_width_matches_percentage()` - Visual accuracy
- [ ] `test_progress_updates()` - Changes on update

**Acceptance Criteria**:
- Progress bars visible
- Percentages accurate
- Updates smoothly

**Demo**:
- Show cards with progress bars

**Commit Message**: `M17: Add progress bars to job cards with percentage display`

---

### **PHASE 5: BACKGROUND PROCESSING (M18-M19)**

#### **M18: Background Job Worker + Single Video Processing** ⏳
**Status**: Not started
**Est. Time**: 2 hours
**Goals**:
- [ ] Create background worker thread
- [ ] Process one job at a time
- [ ] Call existing transcription code
- [ ] Update job progress
- [ ] Handle completion

**Deliverables**:
```
backend/
  ├── worker.py (NEW)
  │   └── BackgroundWorker class
  └── main.py (start worker on startup)
```

**Tests to Write**:
- [ ] `test_worker_picks_pending_job()` - Gets next job
- [ ] `test_worker_updates_status_to_processing()` - Status changes
- [ ] `test_worker_calls_transcription()` - Processes video
- [ ] `test_worker_updates_progress()` - Progress increments
- [ ] `test_worker_marks_completed()` - Job finished
- [ ] `test_worker_handles_error()` - Error caught
- [ ] `test_worker_continues_after_error()` - Doesn't crash
- [ ] `test_worker_sleeps_when_no_jobs()` - Idle handling

**Acceptance Criteria**:
- Worker processes jobs
- Job status updates correctly
- Progress tracked
- Errors handled gracefully
- Output files created

**Demo**:
- Add video to queue
- Watch background processing
- Monitor database for status updates
- Show transcription output files

**Commit Message**: `M18: Implement background job worker with transcription processing`

---

#### **M19: WebSocket Connection for Real-Time Updates** ⏳
**Status**: Not started
**Est. Time**: 1.5 hours
**Goals**:
- [ ] Create WebSocket endpoint
- [ ] Send job updates every 1-2 seconds
- [ ] Connect frontend to WebSocket
- [ ] Update UI in real-time
- [ ] Handle reconnection

**Deliverables**:
```
backend/main.py
  GET /ws/queue (WebSocket endpoint)

frontend/src/
  ├── hooks/useQueueWebSocket.ts (NEW)
  └── components/QueuePanel.tsx (use hook)
```

**Tests to Write**:
- [ ] `test_websocket_connection_established()` - Connect works
- [ ] `test_websocket_sends_job_updates()` - Data flowing
- [ ] `test_frontend_receives_updates()` - UI hook gets data
- [ ] `test_progress_updates_in_real_time()` - Progress changes
- [ ] `test_websocket_reconnect_on_disconnect()` - Reconnect works
- [ ] `test_multiple_clients_receive_updates()` - Multi-client

**Acceptance Criteria**:
- WebSocket connection stable
- Updates sent every 1-2 seconds
- UI updates without refresh
- No lag in progress display

**Demo**:
- Add video to queue
- Watch progress update in real-time
- No page refresh needed
- Multiple browser tabs sync

**Commit Message**: `M19: Implement WebSocket for real-time job progress updates`

---

### **PHASE 6: POLISH & RECOVERY (M20)**

#### **M20: Error Handling + Persistence Recovery** ⏳
**Status**: Not started
**Est. Time**: 1.5 hours
**Goals**:
- [ ] Handle transcription errors gracefully
- [ ] Recovery from container crash
- [ ] Retry logic for failed jobs
- [ ] UI error display
- [ ] Detailed error logging

**Deliverables**:
```
backend/
  ├── worker.py (updated with error handling)
  ├── logger.py (NEW - logging setup)
  └── main.py (startup recovery logic)

frontend/src/
  └── components/JobCard.tsx (error state)
```

**Tests to Write**:
- [ ] `test_transcription_failure_caught()` - Error handled
- [ ] `test_failed_job_marked_in_db()` - Status = FAILED
- [ ] `test_queue_continues_after_failure()` - Doesn't stop
- [ ] `test_error_message_logged()` - Logging works
- [ ] `test_container_restart_resumes_queue()` - Persistence
- [ ] `test_orphaned_jobs_detected()` - Cleanup on startup
- [ ] `test_ui_shows_error_state()` - Error displayed
- [ ] `test_retry_logic_works()` - Can retry failed jobs

**Acceptance Criteria**:
- Errors handled gracefully
- Failed jobs visible in UI
- Queue continues processing
- Container restart resumes work
- Error messages helpful

**Demo**:
- Trigger a failure (bad URL)
- Show error in UI
- Queue continues
- Simulate container crash
- Restart and show resume

**Commit Message**: `M20: Implement comprehensive error handling and recovery system`

---

## 📊 TESTING REQUIREMENTS

### Test Structure
```
backend/tests/
  ├── __init__.py
  ├── conftest.py (pytest fixtures)
  ├── test_database.py (M2)
  ├── test_metadata_store.py (M3)
  ├── test_youtube_utils.py (M6)
  ├── test_youtube_extractor.py (M7, M8, M9)
  ├── test_api_endpoints.py (all API endpoints)
  ├── test_worker.py (M18)
  └── test_websocket.py (M19)
```

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio

# Run all tests
pytest backend/tests/ -v --cov=backend

# Run specific test file
pytest backend/tests/test_database.py -v

# Run before commit (required)
pytest backend/tests/ --tb=short
```

---

## 🔄 COMMIT WORKFLOW

For each milestone:

```bash
# 1. Code the feature
# 2. Write tests
# 3. Run tests (MUST PASS)
pytest backend/tests/ -v

# 4. Rebuild Docker (MUST SUCCEED)
docker compose build

# 5. Test Docker (MUST WORK)
docker compose up -d
# ... manual testing ...
docker compose down

# 6. Commit (ONLY IF ALL PASS)
git add .
git commit -m "M[N]: [Milestone Title] - [Brief Description]"

# 7. Git log shows clear progression
git log --oneline
```

---

## 📝 RESUME INSTRUCTIONS

If session terminates:

1. Check this file for current status
2. Look at git log for last completed milestone
3. Check test results for last milestone
4. Continue from next milestone

```bash
# View last commits
git log --oneline | head -10

# Run tests for last milestone
pytest backend/tests/test_[last_milestone].py -v

# Continue from next milestone
```

---

## ✅ FINAL CHECKLIST BEFORE EACH COMMIT

- [ ] Code written for milestone
- [ ] Tests written and passing: `pytest backend/tests/ -v`
- [ ] Docker builds: `docker compose build`
- [ ] Docker runs: `docker compose up -d`
- [ ] Manual demo tested
- [ ] This file updated with status
- [ ] Git commit created
- [ ] Ready for feedback from user

---

## 📞 FEEDBACK & ADJUSTMENTS

After each demo, user can request:
- [ ] Changes to this milestone
- [ ] Skip to different milestone
- [ ] Adjust requirements
- [ ] Slow down / speed up pace

---

**Last Updated**: 2025-12-29
**Current Status**: Ready to start M1
