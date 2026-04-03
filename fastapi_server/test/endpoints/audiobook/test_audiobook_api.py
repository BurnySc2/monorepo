from pathlib import Path

import io
import os

import pytest
from fastapi.testclient import TestClient


def _garage_available() -> bool:
    garage_url = os.getenv("GARAGE_S3_URL", "http://localhost:3900")
    url = garage_url.removeprefix("http://").removeprefix("https://")
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


def test_upload_non_epub_file(test_client_db_reset: TestClient) -> None:
    """POST /api/audiobook/upload with a non-epub file returns 400."""
    fake_file = io.BytesIO(b"not an epub")
    response = test_client_db_reset.post("/api/audiobook/upload", files={"file": ("test.txt", fake_file, "text/plain")})
    assert response.status_code == 400
    assert "error" in response.json()


def test_upload_missing_file(test_client_db_reset: TestClient) -> None:
    """POST /api/audiobook/upload with no file returns 422."""
    response = test_client_db_reset.post("/api/audiobook/upload", files={})
    assert response.status_code == 422


def test_list_books_after_upload(test_client_db_reset: TestClient) -> None:
    """GET /api/audiobook/books returns the uploaded book."""
    _upload_book(test_client_db_reset)
    response = test_client_db_reset.get("/api/audiobook/books")
    assert response.status_code == 200
    books = response.json()
    assert len(books) == 1
    assert books[0]["book_title"] == "Frankenstein; Or, The Modern Prometheus"


def test_uploaded_book_chapter_count(test_client_db_reset: TestClient) -> None:
    """Uploaded book has correct chapter_count matching actual chapters."""
    book_id = _upload_book(test_client_db_reset)
    response = test_client_db_reset.get(f"/api/audiobook/books/{book_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["book"]["chapter_count"] == 31
    assert len(json_data["chapters"]) == 31


@pytest.mark.skipif(not _garage_available(), reason="Garage not available")
def test_get_book(test_client_db_reset: TestClient) -> None:
    """GET /api/audiobook/books/{id} returns book with chapters array. Requires Garage."""
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


def test_delete_book_not_found(test_client_db_reset: TestClient) -> None:
    """DELETE /api/audiobook/books/999 returns 404."""
    response = test_client_db_reset.delete("/api/audiobook/books/999")
    assert response.status_code == 404
    assert response.json() == {"error": "Book not found"}


def test_delete_book_twice(test_client_db_reset: TestClient) -> None:
    """Deleting a book twice returns 404 on the second attempt."""
    book_id = _upload_book(test_client_db_reset)
    response = test_client_db_reset.delete(f"/api/audiobook/books/{book_id}")
    assert response.status_code == 200

    response = test_client_db_reset.delete(f"/api/audiobook/books/{book_id}")
    assert response.status_code == 404
    assert response.json() == {"error": "Book not found"}


def test_deleted_book_not_in_list(test_client_db_reset: TestClient) -> None:
    """Soft-deleted book does not appear in GET /books list."""
    book_id = _upload_book(test_client_db_reset)
    response = test_client_db_reset.get("/api/audiobook/books")
    assert len(response.json()) == 1

    test_client_db_reset.delete(f"/api/audiobook/books/{book_id}")

    response = test_client_db_reset.get("/api/audiobook/books")
    assert response.json() == []
