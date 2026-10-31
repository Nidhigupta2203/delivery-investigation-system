from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test that GET / returns 200 and expected greeting metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to Delivery Investigation System API"
    assert data["status"] == "online"
    assert data["version"] == "0.1.0"
    assert "docs_url" in data


def test_health_endpoint(client: TestClient):
    """Test that GET /health returns 200, healthy status, and connected database."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "environment" in data


def test_swagger_docs(client: TestClient):
    """Test that the Swagger docs endpoint is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_openapi_json(client: TestClient):
    """Test that OpenAPI schema is properly served."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Delivery Investigation System"
    assert "/health" in schema["paths"]
    assert "/" in schema["paths"]
