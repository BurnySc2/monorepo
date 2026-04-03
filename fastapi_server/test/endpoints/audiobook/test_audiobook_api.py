from pathlib import Path

import os

import pytest
from fastapi.testclient import TestClient


def _minio_available() -> bool:
    minio_url = os.getenv("MINIO_URL", "http://localhost:9000")
    url = minio_url.removeprefix("http://").removeprefix("https://")
    host, port = url.split(":")
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        result = sock.connect_ex((host, int(port)))
        sock.close()
        return result == 0
    except Exception:
        return False


def _upload_book(client: TestClient) -> int:
    book_path = Path(__file__).parent / "actual_books/frankenstein.epub"
    with book_path.open("rb") as f:
        response = client.post("/api/audiobook/upload", files={"file": f})
    assert response.status_code == 201
    return response.json()["id"]


def test_list_books_empty(test_client_db_reset: TestClient) -> None:
    """GET /api/audiobook/books returns empty list initially."""
    response = test_client_db_reset.get("/api/audiobook/books")
    assert response.status_code == 200
    assert response.json() == []


def test_upload_epub(test_client_db_reset: TestClient) -> None:
    """POST /api/audiobook/upload with frankenstein.epub returns 201 with id and title."""
    book_id = _upload_book(test_client_db_reset)
    assert book_id == 1


def test_list_books_after_upload(test_client_db_reset: TestClient) -> None:
    """GET /api/audiobook/books returns the uploaded book."""
    _upload_book(test_client_db_reset)
    response = test_client_db_reset.get("/api/audiobook/books")
    assert response.status_code == 200
    books = response.json()
    assert len(books) == 1
    assert books[0]["book_title"] == "Frankenstein; Or, The Modern Prometheus"


@pytest.mark.skipif(not _minio_available(), reason="MinIO not available")
def test_get_book(test_client_db_reset: TestClient) -> None:
    """GET /api/audiobook/books/{id} returns book with chapters array. Requires MinIO."""
    book_id = _upload_book(test_client_db_reset)
    response = test_client_db_reset.get(f"/api/audiobook/books/{book_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert "book" in json_data
    assert "chapters" in json_data
    assert isinstance(json_data["chapters"], list)
    assert json_data["book"]["book_title"] == "Frankenstein; Or, The Modern Prometheus"
    assert len(json_data["chapters"]) == 31


def test_get_book_not_found(test_client_db_reset: TestClient) -> None:
    """GET /api/audiobook/books/999 returns 404."""
    response = test_client_db_reset.get("/api/audiobook/books/999")
    assert response.status_code == 404
    assert response.json() == {"error": "Book not found"}


def test_delete_book(test_client_db_reset: TestClient) -> None:
    """DELETE /api/audiobook/books/1 returns 200, book is gone."""
    book_id = _upload_book(test_client_db_reset)
    response = test_client_db_reset.delete(f"/api/audiobook/books/{book_id}")
    assert response.status_code == 200
    assert response.json() == {"deleted": True}

    response = test_client_db_reset.get(f"/api/audiobook/books/{book_id}")
    assert response.status_code == 404

    response = test_client_db_reset.get("/api/audiobook/books")
    assert response.status_code == 200
    assert response.json() == []
