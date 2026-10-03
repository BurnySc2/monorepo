import io
import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from components.audiobook.epub_reader import extract_chapters, extract_metadata
from components.pdf_to_epub.chapters import NoChaptersError
from components.pdf_to_epub.epub_writer import roundtrip_validate
from main import app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def _read_fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def _epub_chapter_titles(epub_bytes: bytes) -> list[str]:
    chapters = extract_chapters(io.BytesIO(epub_bytes))
    return [chapter.chapter_title for chapter in chapters if chapter.chapter_title != "nav"]


def test_preview_truncation_single(client: TestClient) -> None:
    data = _read_fixture("small_text.pdf")
    response = client.post(
        "/api/pdf_to_epub/preview",
        files={"file": ("small_text.pdf", data, "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["chapter_source"] == "single"
    assert body["outline"] == []
    assert len(body["chapters"]) == 1
    chapter = body["chapters"][0]
    assert chapter["chars"] > 500
    assert len(chapter["preview"]) == 500
    assert chapter["chars"] == 1239 or chapter["chars"] > len(chapter["preview"])
    assert any("single-chapter" in warning for warning in body["warnings"])


def test_preview_outline_success(client: TestClient) -> None:
    data = _read_fixture("outline.pdf")
    response = client.post(
        "/api/pdf_to_epub/preview",
        files={"file": ("outline.pdf", data, "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["chapter_source"] == "outline"
    assert body["outline"] == ["Chapter 1", "Chapter 2"]
    assert len(body["chapters"]) == 2
    for chapter in body["chapters"]:
        assert chapter["chars"] > 0
        assert len(chapter["preview"]) <= 500
        assert chapter["preview"]


def test_convert_success_magic(client: TestClient) -> None:
    data = _read_fixture("outline.pdf")
    response = client.post(
        "/api/pdf_to_epub/convert",
        files={"file": ("outline.pdf", data, "application/pdf")},
        data={"title": "Test Book", "author": "Test Author", "language": "en"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/epub+zip"
    disposition = response.headers["content-disposition"]
    assert "attachment" in disposition
    assert ".epub" in disposition
    assert "Test Book" in disposition
    assert response.content[:4] == b"PK\x03\x04"


def test_convert_defaults_to_probe_metadata(client: TestClient) -> None:
    data = _read_fixture("small_text.pdf")
    response = client.post(
        "/api/pdf_to_epub/convert",
        files={"file": ("small_text.pdf", data, "application/pdf")},
    )
    assert response.status_code == 200
    assert response.content[:4] == b"PK\x03\x04"
    assert ".epub" in response.headers["content-disposition"]


def test_preview_too_large_rejected(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("routes.pdf_to_epub.MAX_PDF_SIZE_BYTES", 10)
    data = _read_fixture("small_text.pdf")
    response = client.post(
        "/api/pdf_to_epub/preview",
        files={"file": ("small_text.pdf", data, "application/pdf")},
    )
    assert response.status_code == 413


def test_convert_too_large_rejected(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("routes.pdf_to_epub.MAX_PDF_SIZE_BYTES", 10)
    data = _read_fixture("small_text.pdf")
    response = client.post(
        "/api/pdf_to_epub/convert",
        files={"file": ("small_text.pdf", data, "application/pdf")},
    )
    assert response.status_code == 413


def test_preview_not_pdf_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/pdf_to_epub/preview",
        files={"file": ("notes.txt", b"just some text, not a pdf", "text/plain")},
    )
    assert response.status_code == 415


def test_convert_not_pdf_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/pdf_to_epub/convert",
        files={"file": ("notes.txt", b"just some text, not a pdf", "text/plain")},
    )
    assert response.status_code == 415


def test_preview_scanned_rejected(client: TestClient) -> None:
    data = _read_fixture("scanned_image.pdf")
    response = client.post(
        "/api/pdf_to_epub/preview",
        files={"file": ("scanned_image.pdf", data, "application/pdf")},
    )
    assert response.status_code == 422


def test_convert_scanned_rejected(client: TestClient) -> None:
    data = _read_fixture("scanned_image.pdf")
    response = client.post(
        "/api/pdf_to_epub/convert",
        files={"file": ("scanned_image.pdf", data, "application/pdf")},
    )
    assert response.status_code == 422


def test_preview_encrypted_rejected(client: TestClient) -> None:
    data = _read_fixture("encrypted.pdf")
    response = client.post(
        "/api/pdf_to_epub/preview",
        files={"file": ("encrypted.pdf", data, "application/pdf")},
    )
    assert response.status_code == 422
    assert "encrypted" in response.json()["detail"].lower()


def test_convert_encrypted_rejected(client: TestClient) -> None:
    data = _read_fixture("encrypted.pdf")
    response = client.post(
        "/api/pdf_to_epub/convert",
        files={"file": ("encrypted.pdf", data, "application/pdf")},
    )
    assert response.status_code == 422


def test_preview_invalid_range_400(client: TestClient) -> None:
    data = _read_fixture("small_text.pdf")
    response = client.post(
        "/api/pdf_to_epub/preview",
        files={"file": ("small_text.pdf", data, "application/pdf")},
        data={"page_start": "99"},
    )
    assert response.status_code == 400
    swapped = client.post(
        "/api/pdf_to_epub/preview",
        files={"file": ("small_text.pdf", data, "application/pdf")},
        data={"page_start": "2", "page_end": "1"},
    )
    assert swapped.status_code == 400


def test_convert_invalid_range_400(client: TestClient) -> None:
    data = _read_fixture("small_text.pdf")
    response = client.post(
        "/api/pdf_to_epub/convert",
        files={"file": ("small_text.pdf", data, "application/pdf")},
        data={"page_start": "99"},
    )
    assert response.status_code == 400


def test_preview_outline_missing_fallback_warns(client: TestClient) -> None:
    data = _read_fixture("small_text.pdf")
    response = client.post(
        "/api/pdf_to_epub/preview",
        files={"file": ("small_text.pdf", data, "application/pdf")},
        data={"chapter_mode": "outline"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["chapter_source"] != "outline"
    assert any("outline" in warning.lower() for warning in body["warnings"])
    assert any("fell back" in warning.lower() or "fallback" in warning.lower() for warning in body["warnings"])


def test_preview_no_chapters_422(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise_no_chapters(*args: object, **kwargs: object) -> object:
        raise NoChaptersError("no chapters recoverable: empty document")

    monkeypatch.setattr("routes.pdf_to_epub.detect_chapters", _raise_no_chapters)
    data = _read_fixture("small_text.pdf")
    response = client.post(
        "/api/pdf_to_epub/preview",
        files={"file": ("small_text.pdf", data, "application/pdf")},
    )
    assert response.status_code == 422
    assert "no chapters" in response.json()["detail"].lower()


def test_convert_no_chapters_422(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise_no_chapters(*args: object, **kwargs: object) -> object:
        raise NoChaptersError("no chapters recoverable: empty document")

    monkeypatch.setattr("routes.pdf_to_epub.detect_chapters", _raise_no_chapters)
    data = _read_fixture("small_text.pdf")
    response = client.post(
        "/api/pdf_to_epub/convert",
        files={"file": ("small_text.pdf", data, "application/pdf")},
    )
    assert response.status_code == 422
    assert "no chapters" in response.json()["detail"].lower()


def test_preview_corrupt_pdf_fallback_400(client: TestClient) -> None:
    response = client.post(
        "/api/pdf_to_epub/preview",
        files={"file": ("broken.pdf", b"%PDF-1.4 corrupt and truncated", "application/pdf")},
    )
    assert response.status_code == 400


def test_convert_corrupt_pdf_fallback_400(client: TestClient) -> None:
    response = client.post(
        "/api/pdf_to_epub/convert",
        files={"file": ("broken.pdf", b"%PDF-1.4 corrupt and truncated", "application/pdf")},
    )
    assert response.status_code == 400


def test_convert_chapter_titles_rename_happy(client: TestClient) -> None:
    data = _read_fixture("outline.pdf")
    renamed = ["Alpha Intro", "Beta Outro"]
    response = client.post(
        "/api/pdf_to_epub/convert",
        files={"file": ("outline.pdf", data, "application/pdf")},
        data={
            "title": "Rename Book",
            "author": "Rename Author",
            "language": "en",
            "chapter_titles": json.dumps(renamed),
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/epub+zip"
    assert response.content[:4] == b"PK\x03\x04"
    assert _epub_chapter_titles(response.content) == renamed
    metadata = extract_metadata(io.BytesIO(response.content))
    assert metadata.title == "Rename Book"
    roundtrip_validate(response.content, "Rename Book", "Rename Author", renamed)


def test_convert_chapter_titles_length_mismatch_400(client: TestClient) -> None:
    data = _read_fixture("outline.pdf")
    response = client.post(
        "/api/pdf_to_epub/convert",
        files={"file": ("outline.pdf", data, "application/pdf")},
        data={"chapter_titles": json.dumps(["Only One"])},
    )
    assert response.status_code == 400


def test_convert_chapter_titles_malformed_json_400(client: TestClient) -> None:
    data = _read_fixture("outline.pdf")
    response = client.post(
        "/api/pdf_to_epub/convert",
        files={"file": ("outline.pdf", data, "application/pdf")},
        data={"chapter_titles": "not-json{{{ "},
    )
    assert response.status_code == 400


def test_convert_chapter_titles_non_string_entry_400(client: TestClient) -> None:
    data = _read_fixture("outline.pdf")
    response = client.post(
        "/api/pdf_to_epub/convert",
        files={"file": ("outline.pdf", data, "application/pdf")},
        data={"chapter_titles": json.dumps(["Alpha Intro", 123])},
    )
    assert response.status_code == 400


def test_convert_chapter_titles_blank_fallback_keeps_original(client: TestClient) -> None:
    data = _read_fixture("outline.pdf")
    baseline = client.post(
        "/api/pdf_to_epub/convert",
        files={"file": ("outline.pdf", data, "application/pdf")},
    )
    assert baseline.status_code == 200
    original_titles = _epub_chapter_titles(baseline.content)
    assert len(original_titles) == 2
    response = client.post(
        "/api/pdf_to_epub/convert",
        files={"file": ("outline.pdf", data, "application/pdf")},
        data={"chapter_titles": json.dumps(["   ", "Beta Outro"])},
    )
    assert response.status_code == 200
    assert response.content[:4] == b"PK\x03\x04"
    assert _epub_chapter_titles(response.content) == [original_titles[0], "Beta Outro"]


def test_convert_without_chapter_titles_regression(client: TestClient) -> None:
    data = _read_fixture("outline.pdf")
    response = client.post(
        "/api/pdf_to_epub/convert",
        files={"file": ("outline.pdf", data, "application/pdf")},
    )
    assert response.status_code == 200
    assert response.content[:4] == b"PK\x03\x04"
    assert _epub_chapter_titles(response.content) == ["Chapter 1", "Chapter 2"]
