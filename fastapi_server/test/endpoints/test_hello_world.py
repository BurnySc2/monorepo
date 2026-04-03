import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "FastAPI server is running"}


def test_hello_world(client):
    response = client.get("/api/hello_world")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}


def test_rick_morty(client):
    response = client.get("/api/rick_morty")
    assert response.status_code == 200
    assert response.json() == [{"username": "Rick"}, {"username": "Morty"}]
