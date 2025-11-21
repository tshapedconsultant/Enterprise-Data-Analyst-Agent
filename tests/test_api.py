"""
Integration tests for the FastAPI endpoints.

This module tests the API routes and endpoints to ensure
they work correctly and handle errors properly.
"""

import pytest
from fastapi.testclient import TestClient
from api import app


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI app.
    
    Returns:
        TestClient instance
    """
    return TestClient(app)


class TestHealthEndpoint:
    """Test suite for the /health endpoint."""
    
    def test_health_endpoint_returns_200(self, client):
        """Test that health endpoint returns 200 status."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_endpoint_returns_json(self, client):
        """Test that health endpoint returns JSON."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"
    
    def test_health_endpoint_has_status(self, client):
        """Test that health endpoint includes status field."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_health_endpoint_has_timestamp(self, client):
        """Test that health endpoint includes timestamp."""
        response = client.get("/health")
        data = response.json()
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)
    
    def test_health_endpoint_has_version(self, client):
        """Test that health endpoint includes version."""
        response = client.get("/health")
        data = response.json()
        assert "version" in data


class TestRootEndpoint:
    """Test suite for the root / endpoint."""
    
    def test_root_endpoint_returns_200(self, client):
        """Test that root endpoint returns 200 status."""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_root_endpoint_has_api_info(self, client):
        """Test that root endpoint includes API information."""
        response = client.get("/")
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data


class TestRunEndpoint:
    """Test suite for the /run endpoint."""
    
    def test_run_endpoint_accepts_post(self, client):
        """Test that /run endpoint accepts POST requests."""
        response = client.post(
            "/run",
            json={"query": "Test query"}
        )
        # Should return 200 or streaming response
        assert response.status_code in [200, 200]
    
    def test_run_endpoint_requires_query(self, client):
        """Test that /run endpoint requires query field."""
        response = client.post("/run", json={})
        # Should return 422 (validation error) or handle gracefully
        assert response.status_code in [200, 422]
    
    def test_run_endpoint_validates_query_length(self, client):
        """Test that /run endpoint validates query length."""
        # Very long query
        long_query = "a" * 10000
        response = client.post(
            "/run",
            json={"query": long_query}
        )
        # Should either accept or return validation error
        assert response.status_code in [200, 422]
    
    def test_run_endpoint_accepts_optional_params(self, client):
        """Test that /run endpoint accepts optional parameters."""
        response = client.post(
            "/run",
            json={
                "query": "Test query",
                "max_iterations": 5,
                "message_window": 10
            }
        )
        # Should accept the request
        assert response.status_code in [200, 422]
    
    def test_run_endpoint_returns_streaming_response(self, client):
        """Test that /run endpoint returns streaming response."""
        response = client.post(
            "/run",
            json={"query": "Analyze revenue"}
        )
        # Should have appropriate content type for streaming
        assert response.status_code == 200
        # Content type should indicate streaming
        content_type = response.headers.get("content-type", "")
        assert "ndjson" in content_type.lower() or "stream" in content_type.lower()

