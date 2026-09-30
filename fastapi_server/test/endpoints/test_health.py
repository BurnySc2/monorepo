"""Health endpoint tests (liveness probes for Docker / compose)."""

from fastapi.testclient import TestClient


def test_root(test_client: TestClient) -> None:
    """GET / returns running message."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "FastAPI server is running"}


def test_health(test_client: TestClient) -> None:
    """GET /health returns ok status for Docker healthchecks."""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
