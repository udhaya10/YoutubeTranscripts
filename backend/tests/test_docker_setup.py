"""
Tests for Docker Compose setup - Milestone 5
"""
import pytest
import yaml
from pathlib import Path
import subprocess
import sys


@pytest.fixture
def docker_compose_path():
    """Get docker-compose.yml path"""
    return Path(__file__).parent.parent.parent / "docker-compose.yml"


@pytest.fixture
def docker_compose_config(docker_compose_path):
    """Load docker-compose.yml"""
    with open(docker_compose_path, 'r') as f:
        return yaml.safe_load(f)


class TestDockerComposeStructure:
    """Tests for docker-compose.yml structure"""

    def test_docker_compose_file_exists(self, docker_compose_path):
        """Test that docker-compose.yml exists"""
        assert docker_compose_path.exists()
        assert docker_compose_path.is_file()

    def test_docker_compose_valid_yaml(self, docker_compose_path):
        """Test that docker-compose.yml is valid YAML"""
        with open(docker_compose_path, 'r') as f:
            config = yaml.safe_load(f)
        assert config is not None
        assert isinstance(config, dict)

    def test_docker_compose_has_version(self, docker_compose_config):
        """Test that docker-compose has version"""
        assert "version" in docker_compose_config
        assert docker_compose_config["version"] == "3.8"

    def test_docker_compose_has_services(self, docker_compose_config):
        """Test that docker-compose has services section"""
        assert "services" in docker_compose_config
        assert isinstance(docker_compose_config["services"], dict)

    def test_docker_compose_has_networks(self, docker_compose_config):
        """Test that docker-compose has networks section"""
        assert "networks" in docker_compose_config
        assert "youtube-kb-network" in docker_compose_config["networks"]

    def test_docker_compose_has_volumes(self, docker_compose_config):
        """Test that docker-compose has volumes section"""
        assert "volumes" in docker_compose_config
        assert "whisper-cache" in docker_compose_config["volumes"]


class TestBackendService:
    """Tests for backend service configuration"""

    def test_backend_service_exists(self, docker_compose_config):
        """Test that backend service exists"""
        assert "backend" in docker_compose_config["services"]

    def test_backend_has_build_config(self, docker_compose_config):
        """Test that backend has build configuration"""
        backend = docker_compose_config["services"]["backend"]
        assert "build" in backend
        assert "context" in backend["build"]
        assert "dockerfile" in backend["build"]

    def test_backend_has_image_config(self, docker_compose_config):
        """Test that backend has image configuration"""
        backend = docker_compose_config["services"]["backend"]
        assert "image" in backend
        assert "youtube-kb" in backend["image"]

    def test_backend_has_ports(self, docker_compose_config):
        """Test that backend exposes port 8000"""
        backend = docker_compose_config["services"]["backend"]
        assert "ports" in backend
        assert any("8000" in str(port) for port in backend["ports"])

    def test_backend_has_volumes(self, docker_compose_config):
        """Test that backend has volume mounts"""
        backend = docker_compose_config["services"]["backend"]
        assert "volumes" in backend
        assert len(backend["volumes"]) > 0

    def test_backend_has_environment(self, docker_compose_config):
        """Test that backend has environment variables"""
        backend = docker_compose_config["services"]["backend"]
        assert "environment" in backend
        env = backend["environment"]
        assert "HF_TOKEN" in env or "HF_TOKEN" in str(env)

    def test_backend_has_healthcheck(self, docker_compose_config):
        """Test that backend has health check"""
        backend = docker_compose_config["services"]["backend"]
        assert "healthcheck" in backend
        health = backend["healthcheck"]
        assert "test" in health
        assert "/health" in str(health["test"])

    def test_backend_has_restart_policy(self, docker_compose_config):
        """Test that backend has restart policy"""
        backend = docker_compose_config["services"]["backend"]
        assert "restart" in backend
        assert backend["restart"] == "unless-stopped"

    def test_backend_on_network(self, docker_compose_config):
        """Test that backend is on correct network"""
        backend = docker_compose_config["services"]["backend"]
        assert "networks" in backend
        assert "youtube-kb-network" in backend["networks"]


class TestFrontendService:
    """Tests for frontend service configuration"""

    def test_frontend_service_exists(self, docker_compose_config):
        """Test that frontend service exists"""
        assert "frontend" in docker_compose_config["services"]

    def test_frontend_has_build_config(self, docker_compose_config):
        """Test that frontend has build configuration"""
        frontend = docker_compose_config["services"]["frontend"]
        assert "build" in frontend
        assert "context" in frontend["build"]
        assert "dockerfile" in frontend["build"]
        assert "Dockerfile.dev" in frontend["build"]["dockerfile"]

    def test_frontend_has_ports(self, docker_compose_config):
        """Test that frontend exposes port 3000"""
        frontend = docker_compose_config["services"]["frontend"]
        assert "ports" in frontend
        assert any("3000" in str(port) for port in frontend["ports"])

    def test_frontend_has_volumes(self, docker_compose_config):
        """Test that frontend has volume mounts for hot reload"""
        frontend = docker_compose_config["services"]["frontend"]
        assert "volumes" in frontend
        assert len(frontend["volumes"]) > 0

    def test_frontend_has_environment(self, docker_compose_config):
        """Test that frontend has environment variables"""
        frontend = docker_compose_config["services"]["frontend"]
        assert "environment" in frontend
        assert "VITE_API_URL" in frontend["environment"]

    def test_frontend_has_healthcheck(self, docker_compose_config):
        """Test that frontend has health check"""
        frontend = docker_compose_config["services"]["frontend"]
        assert "healthcheck" in frontend
        health = frontend["healthcheck"]
        assert "test" in health

    def test_frontend_has_restart_policy(self, docker_compose_config):
        """Test that frontend has restart policy"""
        frontend = docker_compose_config["services"]["frontend"]
        assert "restart" in frontend
        assert frontend["restart"] == "unless-stopped"

    def test_frontend_depends_on_backend(self, docker_compose_config):
        """Test that frontend depends on backend"""
        frontend = docker_compose_config["services"]["frontend"]
        assert "depends_on" in frontend
        assert "backend" in frontend["depends_on"]

    def test_frontend_on_network(self, docker_compose_config):
        """Test that frontend is on correct network"""
        frontend = docker_compose_config["services"]["frontend"]
        assert "networks" in frontend
        assert "youtube-kb-network" in frontend["networks"]


class TestServiceCommunication:
    """Tests for service communication setup"""

    def test_services_on_same_network(self, docker_compose_config):
        """Test that all services are on the same network"""
        services = docker_compose_config["services"]
        for service_name, service_config in services.items():
            if "networks" in service_config:
                assert "youtube-kb-network" in service_config["networks"]

    def test_backend_exposed_to_frontend(self, docker_compose_config):
        """Test that frontend can reach backend"""
        backend = docker_compose_config["services"]["backend"]
        frontend = docker_compose_config["services"]["frontend"]

        # Both should be on same network
        backend_networks = set(backend.get("networks", []))
        frontend_networks = set(frontend.get("networks", []))

        assert backend_networks & frontend_networks, "Services not on same network"

    def test_frontend_api_url_correct(self, docker_compose_config):
        """Test that frontend API URL points to backend"""
        frontend = docker_compose_config["services"]["frontend"]
        assert "VITE_API_URL" in frontend["environment"]
        api_url = frontend["environment"]["VITE_API_URL"]
        assert "localhost:8000" in api_url or "backend:8000" in api_url


class TestVolumeMounts:
    """Tests for volume configuration"""

    def test_whisper_cache_volume_configured(self, docker_compose_config):
        """Test that whisper cache volume is configured"""
        volumes = docker_compose_config["volumes"]
        assert "whisper-cache" in volumes
        assert volumes["whisper-cache"]["driver"] == "local"

    def test_backend_transcripts_mounted(self, docker_compose_config):
        """Test that transcripts directory is mounted for backend"""
        backend = docker_compose_config["services"]["backend"]
        volumes = backend["volumes"]
        assert any("transcripts" in str(v) for v in volumes)

    def test_backend_metadata_mounted(self, docker_compose_config):
        """Test that metadata directory is mounted for backend"""
        backend = docker_compose_config["services"]["backend"]
        volumes = backend["volumes"]
        assert any("metadata" in str(v) for v in volumes)

    def test_backend_queue_mounted(self, docker_compose_config):
        """Test that queue directory is mounted for backend"""
        backend = docker_compose_config["services"]["backend"]
        volumes = backend["volumes"]
        assert any("queue" in str(v) for v in volumes)

    def test_frontend_src_mounted(self, docker_compose_config):
        """Test that frontend src is mounted for hot reload"""
        frontend = docker_compose_config["services"]["frontend"]
        volumes = frontend["volumes"]
        assert any("src" in str(v) for v in volumes)


class TestEnvironmentVariables:
    """Tests for environment variable configuration"""

    def test_backend_has_required_env_vars(self, docker_compose_config):
        """Test that backend has all required environment variables"""
        backend = docker_compose_config["services"]["backend"]
        env = backend["environment"]
        env_str = str(env)

        assert "OUTPUT_DIR" in env_str
        assert "METADATA_DIR" in env_str
        assert "QUEUE_DIR" in env_str

    def test_env_vars_set_correctly(self, docker_compose_config):
        """Test that environment variables are set to correct values"""
        backend = docker_compose_config["services"]["backend"]
        env = backend["environment"]

        assert "/app/transcripts" in str(env)
        assert "/app/metadata" in str(env)
        assert "/app/queue" in str(env)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
