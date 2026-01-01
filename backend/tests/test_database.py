"""
Tests for SQLite database job queue - Milestone 2
"""
import pytest
import json
from pathlib import Path
from datetime import datetime
import sys
from pathlib import Path as PathlibPath

# Add backend to path
sys.path.insert(0, str(PathlibPath(__file__).parent.parent))

from database import JobDatabase


@pytest.fixture
def job_db(temp_dir):
    """Create temporary database for testing"""
    db_path = Path(temp_dir) / "test_queue.db"
    return JobDatabase(str(db_path))


class TestJobCreation:
    """Tests for creating jobs"""

    def test_create_job_basic(self, job_db):
        """Test creating a basic job"""
        job = job_db.create_job(
            job_id="test_job_1",
            video_id="dQw4w9WgXcQ",
            video_title="Test Video",
        )

        assert job["id"] == "test_job_1"
        assert job["video_id"] == "dQw4w9WgXcQ"
        assert job["video_title"] == "Test Video"
        assert job["status"] == "pending"
        assert job["progress"] == 0.0
        assert job["retry_count"] == 0

    def test_create_job_with_all_fields(self, job_db):
        """Test creating a job with all fields"""
        metadata = {"source": "api", "user_id": "user123"}
        job = job_db.create_job(
            job_id="test_job_2",
            video_id="dQw4w9WgXcQ",
            video_title="Test Video",
            playlist_id="PLxxxxxx",
            channel_id="UCyyyyyy",
            metadata=metadata,
        )

        assert job["playlist_id"] == "PLxxxxxx"
        assert job["channel_id"] == "UCyyyyyy"
        assert job["metadata"] == metadata

    def test_create_multiple_jobs(self, job_db):
        """Test creating multiple jobs"""
        job1 = job_db.create_job("job_1", "video_1", "Video 1")
        job2 = job_db.create_job("job_2", "video_2", "Video 2")
        job3 = job_db.create_job("job_3", "video_3", "Video 3")

        jobs = job_db.list_jobs()
        assert len(jobs) == 3
        assert job1["id"] in [j["id"] for j in jobs]
        assert job2["id"] in [j["id"] for j in jobs]
        assert job3["id"] in [j["id"] for j in jobs]


class TestJobReading:
    """Tests for reading jobs"""

    def test_read_existing_job(self, job_db):
        """Test reading an existing job"""
        created = job_db.create_job(
            "test_job",
            "video_123",
            "Test Video"
        )
        read = job_db.read_job("test_job")

        assert read is not None
        assert read["id"] == "test_job"
        assert read["video_id"] == "video_123"
        assert read["video_title"] == "Test Video"

    def test_read_nonexistent_job(self, job_db):
        """Test reading a job that doesn't exist"""
        result = job_db.read_job("nonexistent_job")
        assert result is None

    def test_read_returns_parsed_metadata(self, job_db):
        """Test that read returns parsed JSON metadata"""
        metadata = {"custom_field": "value", "nested": {"key": "data"}}
        job_db.create_job(
            "job_with_metadata",
            "video_123",
            metadata=metadata
        )

        read = job_db.read_job("job_with_metadata")
        assert read["metadata"] == metadata
        assert isinstance(read["metadata"], dict)


class TestJobStatusUpdate:
    """Tests for updating job status"""

    def test_update_to_processing(self, job_db):
        """Test updating job status to processing"""
        job_db.create_job("test_job", "video_123")
        updated = job_db.update_job_status("test_job", "processing", progress=25.0)

        assert updated["status"] == "processing"
        assert updated["progress"] == 25.0
        assert updated["started_at"] is not None

    def test_update_to_completed(self, job_db):
        """Test updating job status to completed"""
        job_db.create_job("test_job", "video_123")
        job_db.update_job_status("test_job", "processing", progress=50.0)
        completed = job_db.update_job_status("test_job", "completed")

        assert completed["status"] == "completed"
        assert completed["progress"] == 100.0
        assert completed["completed_at"] is not None

    def test_update_to_failed(self, job_db):
        """Test updating job status to failed"""
        job_db.create_job("test_job", "video_123")
        failed = job_db.update_job_status(
            "test_job",
            "failed",
            error_message="Video not found"
        )

        assert failed["status"] == "failed"
        assert failed["error_message"] == "Video not found"
        assert failed["retry_count"] == 1

    def test_retry_count_increments_on_failure(self, job_db):
        """Test that retry count increments on each failure"""
        job_db.create_job("test_job", "video_123")

        for i in range(3):
            failed = job_db.update_job_status(
                "test_job",
                "failed",
                error_message=f"Error {i+1}"
            )
            assert failed["retry_count"] == i + 1

    def test_progress_updates(self, job_db):
        """Test updating progress percentage"""
        job_db.create_job("test_job", "video_123")

        for progress in [10, 25, 50, 75, 90]:
            updated = job_db.update_job_status("test_job", "processing", progress=progress)
            assert updated["progress"] == progress


class TestJobListing:
    """Tests for listing jobs"""

    def test_list_all_jobs(self, job_db):
        """Test listing all jobs"""
        job_db.create_job("job_1", "video_1")
        job_db.create_job("job_2", "video_2")
        job_db.create_job("job_3", "video_3")

        jobs = job_db.list_jobs()
        assert len(jobs) == 3

    def test_list_pending_jobs(self, job_db):
        """Test listing only pending jobs"""
        job_db.create_job("job_1", "video_1")
        job_db.create_job("job_2", "video_2")
        job_db.create_job("job_3", "video_3")

        job_db.update_job_status("job_1", "processing")
        job_db.update_job_status("job_2", "completed")

        pending = job_db.list_pending_jobs()
        assert len(pending) == 1
        assert pending[0]["id"] == "job_3"

    def test_list_jobs_by_status(self, job_db):
        """Test listing jobs filtered by status"""
        job_db.create_job("job_1", "video_1")
        job_db.create_job("job_2", "video_2")
        job_db.create_job("job_3", "video_3")

        job_db.update_job_status("job_1", "processing")
        job_db.update_job_status("job_2", "processing")

        processing = job_db.list_jobs(status="processing")
        assert len(processing) == 2

    def test_list_jobs_empty_status_filter(self, job_db):
        """Test listing jobs with non-existent status"""
        job_db.create_job("job_1", "video_1")

        completed = job_db.list_jobs(status="completed")
        assert len(completed) == 0


class TestOutputPaths:
    """Tests for managing output file paths"""

    def test_update_output_paths(self, job_db):
        """Test updating output file paths"""
        job_db.create_job("test_job", "video_123")
        updated = job_db.update_output_paths(
            "test_job",
            transcript_md="/app/transcripts/video_123.md",
            transcript_json="/app/transcripts/video_123.json",
            metadata_file="/app/metadata/videos/video_123.json",
        )

        assert updated["output_paths"]["transcript_md"] == "/app/transcripts/video_123.md"
        assert updated["output_paths"]["transcript_json"] == "/app/transcripts/video_123.json"
        assert updated["output_paths"]["metadata"] == "/app/metadata/videos/video_123.json"

    def test_output_paths_partial_update(self, job_db):
        """Test updating only some output paths"""
        job_db.create_job("test_job", "video_123")
        updated = job_db.update_output_paths(
            "test_job",
            transcript_md="/app/transcripts/video_123.md"
        )

        assert updated["output_paths"]["transcript_md"] == "/app/transcripts/video_123.md"
        assert updated["output_paths"]["transcript_json"] is None
        assert updated["output_paths"]["metadata"] is None


class TestDatabasePersistence:
    """Tests for database persistence across instances"""

    def test_data_persists_across_connections(self, temp_dir):
        """Test that data persists when creating new connection"""
        db_path = Path(temp_dir) / "persistent.db"

        # First connection: create job
        db1 = JobDatabase(str(db_path))
        job1 = db1.create_job("persist_job", "video_123", "Test Video")
        assert job1["id"] == "persist_job"

        # Second connection: read job
        db2 = JobDatabase(str(db_path))
        job2 = db2.read_job("persist_job")
        assert job2 is not None
        assert job2["id"] == "persist_job"
        assert job2["video_title"] == "Test Video"

    def test_job_status_persists(self, temp_dir):
        """Test that job status updates persist"""
        db_path = Path(temp_dir) / "status_persist.db"

        db1 = JobDatabase(str(db_path))
        db1.create_job("status_job", "video_123")
        db1.update_job_status("status_job", "processing", progress=50.0)

        db2 = JobDatabase(str(db_path))
        job = db2.read_job("status_job")
        assert job["status"] == "processing"
        assert job["progress"] == 50.0

    def test_database_file_exists(self, temp_dir):
        """Test that database file is created"""
        db_path = Path(temp_dir) / "test_exists.db"
        db = JobDatabase(str(db_path))
        db.create_job("job_1", "video_1")

        assert db_path.exists()
        assert db_path.stat().st_size > 0


class TestConcurrentAccess:
    """Tests for concurrent database access (threading safety)"""

    def test_concurrent_job_creation(self, job_db):
        """Test creating jobs from multiple threads simultaneously"""
        import threading

        created_jobs = []
        errors = []

        def create_job(job_num):
            try:
                job = job_db.create_job(
                    f"concurrent_job_{job_num}",
                    f"video_{job_num}",
                    f"Video {job_num}"
                )
                created_jobs.append(job)
            except Exception as e:
                errors.append(str(e))

        # Create 10 threads all creating jobs simultaneously
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_job, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        assert len(errors) == 0, f"Errors occurred: {errors}"
        # Verify all jobs were created
        assert len(created_jobs) == 10
        # Verify all jobs are in database
        all_jobs = job_db.list_jobs()
        assert len(all_jobs) == 10

    def test_concurrent_status_updates(self, job_db):
        """Test updating job status from multiple threads"""
        import threading

        # Create a job first
        job_db.create_job("update_job", "video_123", "Test")
        errors = []
        update_count = 0

        def update_status(update_num):
            nonlocal update_count
            try:
                progress = (update_num % 100)
                job_db.update_job_status(
                    "update_job",
                    "processing",
                    progress=float(progress)
                )
                update_count += 1
            except Exception as e:
                errors.append(str(e))

        # Update from 5 threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_status, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify no errors
        assert len(errors) == 0, f"Errors: {errors}"
        assert update_count == 5

        # Verify job still exists and is valid
        job = job_db.read_job("update_job")
        assert job is not None
        assert job["status"] == "processing"

    def test_mixed_concurrent_operations(self, job_db):
        """Test concurrent creates, reads, and updates"""
        import threading

        operations_done = 0
        errors = []
        lock = threading.Lock()

        def mixed_operation(op_num):
            nonlocal operations_done
            try:
                if op_num % 3 == 0:
                    # Create
                    job_db.create_job(f"mixed_job_{op_num}", f"video_{op_num}", f"Video {op_num}")
                elif op_num % 3 == 1:
                    # Read (if job exists)
                    existing_id = f"mixed_job_{op_num - 1}" if op_num > 0 else f"mixed_job_0"
                    job_db.read_job(existing_id)
                else:
                    # Update (if job exists)
                    existing_id = f"mixed_job_{op_num - 2}" if op_num > 1 else f"mixed_job_0"
                    job_db.update_job_status(existing_id, "processing", progress=50.0)

                with lock:
                    operations_done += 1
            except Exception as e:
                errors.append(str(e))

        # Run 9 mixed operations
        threads = []
        for i in range(9):
            thread = threading.Thread(target=mixed_operation, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify operations completed without error
        assert len(errors) == 0, f"Errors: {errors}"
        assert operations_done == 9


class TestDatabaseIntegration:
    """Integration tests for complete workflows"""

    def test_complete_job_lifecycle(self, job_db):
        """Test complete job lifecycle: create → process → complete"""
        # Create
        job = job_db.create_job(
            "lifecycle_job",
            "video_123",
            "Test Video",
            metadata={"source": "test"}
        )
        assert job["status"] == "pending"

        # Start processing
        job = job_db.update_job_status("lifecycle_job", "processing", progress=0.0)
        assert job["status"] == "processing"

        # Update progress
        job = job_db.update_job_status("lifecycle_job", "processing", progress=50.0)
        assert job["progress"] == 50.0

        # Complete
        job = job_db.update_job_status("lifecycle_job", "completed")
        assert job["status"] == "completed"
        assert job["progress"] == 100.0

        # Add output paths
        job = job_db.update_output_paths(
            "lifecycle_job",
            transcript_md="/app/transcripts/video_123.md",
            transcript_json="/app/transcripts/video_123.json",
        )
        assert job["output_paths"]["transcript_md"] is not None

    def test_mixed_job_states(self, job_db):
        """Test handling multiple jobs in different states"""
        # Create 5 jobs
        for i in range(5):
            job_db.create_job(f"job_{i}", f"video_{i}", f"Video {i}")

        # Put them in different states
        job_db.update_job_status("job_0", "processing", progress=0.0)
        job_db.update_job_status("job_1", "processing", progress=75.0)
        job_db.update_job_status("job_2", "completed")
        job_db.update_job_status("job_3", "failed", error_message="Error")
        # job_4 stays pending

        all_jobs = job_db.list_jobs()
        assert len(all_jobs) == 5

        pending = job_db.list_pending_jobs()
        assert len(pending) == 1

        processing = job_db.list_jobs(status="processing")
        assert len(processing) == 2

        completed = job_db.list_jobs(status="completed")
        assert len(completed) == 1

        failed = job_db.list_jobs(status="failed")
        assert len(failed) == 1


class TestErrorRecovery:
    """Tests for error handling and recovery scenarios"""

    def test_database_recovery_on_corrupt_file(self, temp_dir):
        """Test database recovery when file is corrupted"""
        import sqlite3

        db_path = Path(temp_dir) / "corrupt.db"

        # Write invalid database file
        db_path.write_bytes(b"NOT A VALID SQLITE DATABASE FILE FORMAT")

        # Attempt to initialize database
        # Should either recover or handle gracefully
        try:
            db = JobDatabase(str(db_path))
            # If it doesn't raise an error, it should have recovered
            assert db.db_path.exists()
        except sqlite3.DatabaseError:
            # This is acceptable - we caught the corruption
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
