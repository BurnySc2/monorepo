from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from components.pdf_to_epub.parser import EncryptedPdfError, ScannedPdfError, probe_pdf
from main import app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def _read_fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_probe_text_pdf_success(client: TestClient) -> None:
    data = _read_fixture("small_text.pdf")
    response = client.post(
        "/api/pdf_to_epub/probe",
        files={"file": ("small_text.pdf", data, "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_pages"] == 2
    assert body["has_outline"] is False
    assert body["has_images"] is False
    assert body["metadata"]["title"] == "Sample Book"
    assert body["metadata"]["author"] == "Sample Author"
    assert body["metadata"]["language"] == "en"


def test_probe_outline_pdf_success(client: TestClient) -> None:
    data = _read_fixture("outline.pdf")
    response = client.post(
        "/api/pdf_to_epub/probe",
        files={"file": ("outline.pdf", data, "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_pages"] == 2
    assert body["has_outline"] is True
    assert body["has_images"] is True
    assert body["metadata"]["title"] == "Outline Book"


def test_probe_scanned_pdf_rejected(client: TestClient) -> None:
    data = _read_fixture("scanned_image.pdf")
    response = client.post(
        "/api/pdf_to_epub/probe",
        files={"file": ("scanned_image.pdf", data, "application/pdf")},
    )
    assert response.status_code == 422
    assert "extractable" in response.json()["detail"].lower() or "scanned" in response.json()["detail"].lower()


def test_probe_encrypted_pdf_rejected(client: TestClient) -> None:
    data = _read_fixture("encrypted.pdf")
    response = client.post(
        "/api/pdf_to_epub/probe",
        files={"file": ("encrypted.pdf", data, "application/pdf")},
    )
    assert response.status_code == 422
    assert "encrypted" in response.json()["detail"].lower()


def test_probe_not_pdf_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/pdf_to_epub/probe",
        files={"file": ("notes.txt", b"just some text, not a pdf", "text/plain")},
    )
    assert response.status_code == 415


def test_probe_corrupt_pdf_fallback_400(client: TestClient) -> None:
    response = client.post(
        "/api/pdf_to_epub/probe",
        files={"file": ("broken.pdf", b"%PDF-1.4 corrupt and truncated", "application/pdf")},
    )
    assert response.status_code == 400


def test_probe_too_large_rejected(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("routes.pdf_to_epub.MAX_PDF_SIZE_BYTES", 10)
    data = _read_fixture("small_text.pdf")
    response = client.post(
        "/api/pdf_to_epub/probe",
        files={"file": ("small_text.pdf", data, "application/pdf")},
    )
    assert response.status_code == 413


def test_probe_pdf_unit_text() -> None:
    result = probe_pdf(_read_fixture("small_text.pdf"))
    assert result.total_pages == 2
    assert result.has_outline is False
    assert result.has_images is False
    assert result.metadata.title == "Sample Book"


def test_probe_pdf_unit_scanned_raises() -> None:
    with pytest.raises(ScannedPdfError):
        probe_pdf(_read_fixture("scanned_image.pdf"))


def test_probe_pdf_unit_encrypted_raises() -> None:
    with pytest.raises(EncryptedPdfError):
        probe_pdf(_read_fixture("encrypted.pdf"))
