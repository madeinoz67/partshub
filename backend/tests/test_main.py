"""
Basic tests for main application
"""

from fastapi.testclient import TestClient
from backend.src.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns API information"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "PartsHub API"
    assert data["version"] == "0.1.0"
    assert data["docs"] == "/docs"


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_openapi_docs():
    """Test OpenAPI documentation is available"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc_docs():
    """Test ReDoc documentation is available"""
    response = client.get("/redoc")
    assert response.status_code == 200
