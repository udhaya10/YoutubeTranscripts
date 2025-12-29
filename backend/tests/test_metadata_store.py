"""
Tests for file-based metadata storage - Milestone 3
"""
import pytest
import json
from pathlib import Path
import sys
from pathlib import Path as PathlibPath

# Add backend to path
sys.path.insert(0, str(PathlibPath(__file__).parent.parent))

from metadata_store import MetadataStore


@pytest.fixture
def metadata_store(temp_dir):
    """Create temporary metadata store for testing"""
    store_path = Path(temp_dir) / "metadata"
    return MetadataStore(str(store_path))


class TestChannelMetadata:
    """Tests for channel metadata operations"""

    def test_save_channel_metadata(self, metadata_store):
        """Test saving channel metadata"""
        channel_data = {
            "id": "UCuAXFkgsw1L7xaCfnd5JJOw",
            "title": "Rick Astley",
            "description": "Official Rick Astley channel",
            "playlist_count": 5,
            "video_count": 100,
        }

        paths = metadata_store.save_channel_metadata(
            "UCuAXFkgsw1L7xaCfnd5JJOw",
            channel_data
        )

        assert paths["json"].exists()
        assert paths["markdown"].exists()
        assert "channel_" in str(paths["json"])
        assert ".json" in str(paths["json"])

    def test_save_channel_creates_json_file(self, metadata_store):
        """Test that saving channel creates valid JSON file"""
        channel_data = {
            "id": "UC123456",
            "title": "Test Channel",
            "description": "Test description",
        }

        metadata_store.save_channel_metadata("UC123456", channel_data)

        json_path = metadata_store.base_path / "channels" / "channel_UC123456.json"
        with open(json_path, "r") as f:
            loaded = json.load(f)

        assert loaded["title"] == "Test Channel"
        assert loaded["_type"] == "channel"
        assert "_saved_at" in loaded

    def test_save_channel_creates_markdown_file(self, metadata_store):
        """Test that saving channel creates Markdown file"""
        channel_data = {
            "id": "UC123456",
            "title": "Test Channel",
            "description": "Test description",
        }

        metadata_store.save_channel_metadata("UC123456", channel_data)

        md_path = metadata_store.base_path / "channels" / "channel_UC123456.md"
        assert md_path.exists()

        with open(md_path, "r") as f:
            content = f.read()

        assert "Test Channel" in content
        assert "UC123456" in content
        assert "Test description" in content

    def test_load_channel_metadata(self, metadata_store):
        """Test loading channel metadata"""
        original_data = {
            "id": "UC123456",
            "title": "Test Channel",
            "description": "Test description",
        }

        metadata_store.save_channel_metadata("UC123456", original_data)
        loaded = metadata_store.load_channel_metadata("UC123456")

        assert loaded["title"] == "Test Channel"
        assert loaded["description"] == "Test description"

    def test_load_nonexistent_channel(self, metadata_store):
        """Test loading non-existent channel returns None"""
        result = metadata_store.load_channel_metadata("NONEXISTENT")
        assert result is None

    def test_channel_exists_check(self, metadata_store):
        """Test checking if channel exists"""
        assert not metadata_store.channel_exists("UC123456")

        channel_data = {"id": "UC123456", "title": "Test"}
        metadata_store.save_channel_metadata("UC123456", channel_data)

        assert metadata_store.channel_exists("UC123456")


class TestPlaylistMetadata:
    """Tests for playlist metadata operations"""

    def test_save_playlist_metadata(self, metadata_store):
        """Test saving playlist metadata"""
        playlist_data = {
            "id": "PLxxxxxx",
            "title": "Greatest Hits",
            "channel": "Rick Astley",
            "video_count": 50,
            "description": "Best songs",
        }

        paths = metadata_store.save_playlist_metadata("PLxxxxxx", playlist_data)

        assert paths["json"].exists()
        assert paths["markdown"].exists()

    def test_save_playlist_creates_json_file(self, metadata_store):
        """Test that saving playlist creates valid JSON file"""
        playlist_data = {
            "id": "PL123456",
            "title": "Test Playlist",
            "channel": "Test Channel",
        }

        metadata_store.save_playlist_metadata("PL123456", playlist_data)

        json_path = metadata_store.base_path / "playlists" / "playlist_PL123456.json"
        with open(json_path, "r") as f:
            loaded = json.load(f)

        assert loaded["title"] == "Test Playlist"
        assert loaded["_type"] == "playlist"

    def test_save_playlist_creates_markdown_file(self, metadata_store):
        """Test that saving playlist creates Markdown file"""
        playlist_data = {
            "id": "PL123456",
            "title": "Test Playlist",
            "channel": "Test Channel",
            "video_count": 25,
        }

        metadata_store.save_playlist_metadata("PL123456", playlist_data)

        md_path = metadata_store.base_path / "playlists" / "playlist_PL123456.md"
        assert md_path.exists()

        with open(md_path, "r") as f:
            content = f.read()

        assert "Test Playlist" in content
        assert "PL123456" in content

    def test_load_playlist_metadata(self, metadata_store):
        """Test loading playlist metadata"""
        original_data = {
            "id": "PL123456",
            "title": "Test Playlist",
            "channel": "Test Channel",
        }

        metadata_store.save_playlist_metadata("PL123456", original_data)
        loaded = metadata_store.load_playlist_metadata("PL123456")

        assert loaded["title"] == "Test Playlist"

    def test_playlist_exists_check(self, metadata_store):
        """Test checking if playlist exists"""
        assert not metadata_store.playlist_exists("PL123456")

        playlist_data = {"id": "PL123456", "title": "Test"}
        metadata_store.save_playlist_metadata("PL123456", playlist_data)

        assert metadata_store.playlist_exists("PL123456")


class TestVideoMetadata:
    """Tests for video metadata operations"""

    def test_save_video_metadata(self, metadata_store):
        """Test saving video metadata"""
        video_data = {
            "id": "dQw4w9WgXcQ",
            "title": "Never Gonna Give You Up",
            "uploader": "Rick Astley",
            "duration": 213,
            "description": "Official music video",
        }

        paths = metadata_store.save_video_metadata("dQw4w9WgXcQ", video_data)

        assert paths["json"].exists()
        assert paths["markdown"].exists()

    def test_save_video_creates_json_file(self, metadata_store):
        """Test that saving video creates valid JSON file"""
        video_data = {
            "id": "vid123456",
            "title": "Test Video",
            "uploader": "Test Uploader",
            "duration": 300,
        }

        metadata_store.save_video_metadata("vid123456", video_data)

        json_path = metadata_store.base_path / "videos" / "video_vid123456.json"
        with open(json_path, "r") as f:
            loaded = json.load(f)

        assert loaded["title"] == "Test Video"
        assert loaded["_type"] == "video"
        assert loaded["duration"] == 300

    def test_save_video_creates_markdown_file(self, metadata_store):
        """Test that saving video creates Markdown file"""
        video_data = {
            "id": "vid123456",
            "title": "Test Video",
            "uploader": "Test Uploader",
            "duration": 300,
        }

        metadata_store.save_video_metadata("vid123456", video_data)

        md_path = metadata_store.base_path / "videos" / "video_vid123456.md"
        assert md_path.exists()

        with open(md_path, "r") as f:
            content = f.read()

        assert "Test Video" in content
        assert "vid123456" in content

    def test_load_video_metadata(self, metadata_store):
        """Test loading video metadata"""
        original_data = {
            "id": "vid123456",
            "title": "Test Video",
            "uploader": "Test Uploader",
            "duration": 300,
        }

        metadata_store.save_video_metadata("vid123456", original_data)
        loaded = metadata_store.load_video_metadata("vid123456")

        assert loaded["title"] == "Test Video"
        assert loaded["duration"] == 300

    def test_video_exists_check(self, metadata_store):
        """Test checking if video exists"""
        assert not metadata_store.video_exists("vid123456")

        video_data = {"id": "vid123456", "title": "Test"}
        metadata_store.save_video_metadata("vid123456", video_data)

        assert metadata_store.video_exists("vid123456")


class TestMetadataListing:
    """Tests for listing saved metadata"""

    def test_list_channel_ids(self, metadata_store):
        """Test listing all channel IDs"""
        channels = [
            ("UC123456", {"id": "UC123456", "title": "Channel 1"}),
            ("UC789012", {"id": "UC789012", "title": "Channel 2"}),
        ]

        for channel_id, data in channels:
            metadata_store.save_channel_metadata(channel_id, data)

        ids = metadata_store.list_channel_ids()
        assert len(ids) == 2
        assert "UC123456" in ids
        assert "UC789012" in ids

    def test_list_playlist_ids(self, metadata_store):
        """Test listing all playlist IDs"""
        playlists = [
            ("PL111111", {"id": "PL111111", "title": "Playlist 1"}),
            ("PL222222", {"id": "PL222222", "title": "Playlist 2"}),
        ]

        for playlist_id, data in playlists:
            metadata_store.save_playlist_metadata(playlist_id, data)

        ids = metadata_store.list_playlist_ids()
        assert len(ids) == 2
        assert "PL111111" in ids
        assert "PL222222" in ids

    def test_list_video_ids(self, metadata_store):
        """Test listing all video IDs"""
        videos = [
            ("vid111111", {"id": "vid111111", "title": "Video 1", "duration": 100}),
            ("vid222222", {"id": "vid222222", "title": "Video 2", "duration": 200}),
        ]

        for video_id, data in videos:
            metadata_store.save_video_metadata(video_id, data)

        ids = metadata_store.list_video_ids()
        assert len(ids) == 2
        assert "vid111111" in ids
        assert "vid222222" in ids


class TestDirectoryStructure:
    """Tests for directory structure management"""

    def test_directories_created_on_init(self, temp_dir):
        """Test that required directories are created on init"""
        store_path = Path(temp_dir) / "new_metadata"
        store = MetadataStore(str(store_path))

        assert (store_path / "channels").exists()
        assert (store_path / "playlists").exists()
        assert (store_path / "videos").exists()

    def test_metadata_files_in_correct_directories(self, metadata_store):
        """Test that metadata files are saved in correct directories"""
        metadata_store.save_channel_metadata("UC123", {"id": "UC123", "title": "Ch"})
        metadata_store.save_playlist_metadata("PL456", {"id": "PL456", "title": "Pl"})
        metadata_store.save_video_metadata("vid789", {"id": "vid789", "title": "V", "duration": 100})

        channels_dir = metadata_store.base_path / "channels"
        playlists_dir = metadata_store.base_path / "playlists"
        videos_dir = metadata_store.base_path / "videos"

        assert len(list(channels_dir.glob("channel_UC123*"))) == 2  # JSON + MD
        assert len(list(playlists_dir.glob("playlist_PL456*"))) == 2
        assert len(list(videos_dir.glob("video_vid789*"))) == 2


class TestMetadataIntegration:
    """Integration tests for complete workflows"""

    def test_complete_metadata_workflow(self, metadata_store):
        """Test complete workflow: save and load different metadata types"""
        # Save channel
        channel_data = {
            "id": "UC123456",
            "title": "Test Channel",
            "playlist_count": 3,
        }
        metadata_store.save_channel_metadata("UC123456", channel_data)

        # Save playlists
        for i in range(3):
            playlist_data = {
                "id": f"PL{i}",
                "title": f"Playlist {i}",
                "channel": "Test Channel",
                "video_count": 10 + i,
            }
            metadata_store.save_playlist_metadata(f"PL{i}", playlist_data)

        # Save videos
        for i in range(30):
            video_data = {
                "id": f"vid{i:04d}",
                "title": f"Video {i}",
                "uploader": "Test Channel",
                "duration": 100 + i,
            }
            metadata_store.save_video_metadata(f"vid{i:04d}", video_data)

        # Verify counts
        assert len(metadata_store.list_channel_ids()) == 1
        assert len(metadata_store.list_playlist_ids()) == 3
        assert len(metadata_store.list_video_ids()) == 30

        # Verify can load each type
        channel = metadata_store.load_channel_metadata("UC123456")
        assert channel["title"] == "Test Channel"

        playlist = metadata_store.load_playlist_metadata("PL0")
        assert playlist["title"] == "Playlist 0"

        video = metadata_store.load_video_metadata("vid0000")
        assert video["title"] == "Video 0"

    def test_metadata_persistence_across_instances(self, temp_dir):
        """Test that metadata persists across MetadataStore instances"""
        store_path = Path(temp_dir) / "persistent_metadata"

        # First instance: save data
        store1 = MetadataStore(str(store_path))
        video_data = {"id": "vid123", "title": "Persistent Video", "duration": 150}
        store1.save_video_metadata("vid123", video_data)

        # Second instance: load data
        store2 = MetadataStore(str(store_path))
        loaded = store2.load_video_metadata("vid123")
        assert loaded["title"] == "Persistent Video"

    def test_both_json_and_markdown_exist(self, metadata_store):
        """Test that both JSON and Markdown files are created for all types"""
        metadata_store.save_channel_metadata("UC123", {"id": "UC123", "title": "Ch"})
        metadata_store.save_playlist_metadata("PL456", {"id": "PL456", "title": "Pl"})
        metadata_store.save_video_metadata("vid789", {"id": "vid789", "title": "V", "duration": 100})

        # Check all files exist
        assert (metadata_store.base_path / "channels" / "channel_UC123.json").exists()
        assert (metadata_store.base_path / "channels" / "channel_UC123.md").exists()
        assert (metadata_store.base_path / "playlists" / "playlist_PL456.json").exists()
        assert (metadata_store.base_path / "playlists" / "playlist_PL456.md").exists()
        assert (metadata_store.base_path / "videos" / "video_vid789.json").exists()
        assert (metadata_store.base_path / "videos" / "video_vid789.md").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
