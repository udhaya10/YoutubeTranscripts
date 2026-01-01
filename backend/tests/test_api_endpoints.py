"""
Tests for FastAPI endpoints - Milestone 1
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app


@pytest.fixture
def client():
    """Create FastAPI test client"""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint"""

    def test_health_endpoint_returns_200(self, client):
        """Test that health endpoint returns 200 OK"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_returns_json(self, client):
        """Test that health endpoint returns JSON"""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"

    def test_health_endpoint_response_structure(self, client):
        """Test that health endpoint returns correct structure"""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert data["status"] == "healthy"
        assert data["service"] == "youtube-knowledge-base-api"

    def test_health_endpoint_version(self, client):
        """Test that health endpoint returns correct version"""
        response = client.get("/health")
        data = response.json()
        assert data["version"] == "0.1.0"


class TestRootEndpoint:
    """Tests for root endpoint"""

    def test_root_endpoint_returns_200(self, client):
        """Test that root endpoint returns 200 OK"""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_endpoint_returns_json(self, client):
        """Test that root endpoint returns JSON"""
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"

    def test_root_endpoint_response_structure(self, client):
        """Test that root endpoint returns correct structure"""
        response = client.get("/")
        data = response.json()

        assert "message" in data
        assert "docs" in data
        assert "redoc" in data
        assert "version" in data


class TestSwaggerDocs:
    """Tests for Swagger documentation"""

    def test_swagger_ui_endpoint_exists(self, client):
        """Test that Swagger UI endpoint exists"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_swagger_ui_content_type(self, client):
        """Test that Swagger UI returns HTML"""
        response = client.get("/docs")
        assert "text/html" in response.headers["content-type"]

    def test_openapi_schema_endpoint_exists(self, client):
        """Test that OpenAPI schema endpoint exists"""
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_openapi_schema_has_health_endpoint(self, client):
        """Test that OpenAPI schema includes health endpoint"""
        response = client.get("/openapi.json")
        schema = response.json()

        assert "paths" in schema
        assert "/health" in schema["paths"]
        assert "get" in schema["paths"]["/health"]


class TestReDoc:
    """Tests for ReDoc documentation"""

    def test_redoc_endpoint_exists(self, client):
        """Test that ReDoc endpoint exists"""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_redoc_content_type(self, client):
        """Test that ReDoc returns HTML"""
        response = client.get("/redoc")
        assert "text/html" in response.headers["content-type"]


class TestCORSMiddleware:
    """Tests for CORS middleware"""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present"""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        assert "access-control-allow-origin" in response.headers

    def test_cors_allows_all_origins(self, client):
        """Test that CORS allows all origins"""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        assert response.headers["access-control-allow-origin"] == "*"

    def test_preflight_request_succeeds(self, client):
        """Test that preflight request succeeds"""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )
        assert response.status_code == 200

    def test_cors_allows_multiple_origins(self, client):
        """Test CORS with different origins"""
        origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "https://example.com",
        ]
        for origin in origins:
            response = client.get(
                "/health",
                headers={"Origin": origin}
            )
            assert response.headers["access-control-allow-origin"] == "*"

    def test_cors_allow_credentials(self, client):
        """Test that credentials are allowed in CORS"""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        assert "access-control-allow-credentials" in response.headers

    def test_cors_allow_methods(self, client):
        """Test that all methods are allowed"""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            }
        )
        assert response.status_code == 200


class TestDocumentationEndpoints:
    """Tests for API documentation endpoints"""

    def test_redoc_endpoint_html_structure(self, client):
        """Test that ReDoc endpoint returns valid HTML"""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "redoc" in response.text.lower()
        assert "openapi.json" in response.text

    def test_openapi_json_schema_structure(self, client):
        """Test that OpenAPI schema has correct structure"""
        response = client.get("/openapi.json")
        schema = response.json()

        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        assert schema["info"]["title"] == "YouTube Knowledge Base API"
        assert schema["info"]["version"] == "0.1.0"

    def test_openapi_schema_includes_all_endpoints(self, client):
        """Test that OpenAPI schema documents all endpoints"""
        response = client.get("/openapi.json")
        schema = response.json()
        paths = schema["paths"]

        assert "/" in paths
        assert "/health" in paths

    def test_redoc_has_redoc_script(self, client):
        """Test that ReDoc page includes ReDoc JavaScript"""
        response = client.get("/redoc")
        assert "redoc.standalone.js" in response.text


class TestErrorHandling:
    """Tests for error handling"""

    def test_nonexistent_endpoint_returns_404(self, client):
        """Test that non-existent endpoints return 404"""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_invalid_method_returns_405(self, client):
        """Test that invalid HTTP methods return 405"""
        response = client.post("/health")
        assert response.status_code == 405


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
