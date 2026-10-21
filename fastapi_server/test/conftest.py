"""Pytest configuration and shared fixtures.

This module is automatically loaded by pytest (via conftest.py naming).
Fixtures defined here are available to all tests without explicit imports.

Fixtures:
    test_client: FastAPI test client for tests that don't need database.
    test_client_db_reset: FastAPI test client with fresh database tables
        created before each test and dropped after.
"""

import os
import socket
from collections.abc import Iterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient
from piccolo.table import Table, create_db_tables, drop_db_tables
from piccolo.utils.sync import run_sync

from components.audiobook.epub_reader import ensure_nltk_data
from components.login.cookies import LoggedInUser, get_current_user
from main import app
from schemas.audiobook.db_models import AudiobookBook, AudiobookChapter
from settings import settings

TABLES: list[type[Table]] = [AudiobookBook, AudiobookChapter]


def _tcp_open(host: str, port: int, timeout: float = 1.0) -> bool:
    if host in ("0.0.0.0", "::"):
        host = "127.0.0.1"
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def postgres_available() -> bool:
    try:
        parsed = urlparse(settings.postgres_connection_string)
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        return _tcp_open(host, port)
    except Exception:  # noqa: BLE001
        return False


def rustfs_available() -> bool:
    try:
        parsed = urlparse(settings.rustfs_s3_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        return _tcp_open(host, port)
    except Exception:  # noqa: BLE001
        return False


def _require_postgres() -> None:
    if postgres_available():
        return
    reason = "postgres not available"
    if os.getenv("REQUIRE_DB") == "1" or os.getenv("FAIL_ON_SKIP") == "1":
        pytest.fail(reason)
    pytest.skip(reason)


def _require_rustfs() -> None:
    if rustfs_available():
        return
    reason = "RustFS not available"
    if os.getenv("REQUIRE_DB") == "1" or os.getenv("FAIL_ON_SKIP") == "1":
        pytest.fail(reason)
    pytest.skip(reason)


@pytest.fixture(scope="function")
def test_client() -> Iterator[TestClient]:
    with TestClient(app=app) as client:
        yield client


def _mock_get_current_user() -> LoggedInUser:
    return LoggedInUser(id=1, name="testuser", service="github")


@pytest.fixture(scope="function")
def test_client_db_reset() -> Iterator[TestClient]:
    _require_postgres()
    run_sync(create_db_tables(*TABLES, if_not_exists=True))
    app.dependency_overrides[get_current_user] = _mock_get_current_user
    try:
        with TestClient(app=app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        run_sync(drop_db_tables(*TABLES))


@pytest.fixture(scope="function")
def mock_s3(monkeypatch: pytest.MonkeyPatch) -> Iterator[AsyncMock]:
    """Mock S3 presigned URL generation for audiobook tests (no network)."""
    mock_session = AsyncMock()

    @asynccontextmanager
    async def _mock_get_s3_client():  # type: ignore[no-untyped-def]
        yield mock_session

    async def _mock_presigned_url(  # type: ignore[no-untyped-def]
        session=None,
        bucket="",
        key="",
        file_name="",
        expires_in_seconds=3600,
        verify_object_exists=False,
        disposition="attachment",
    ) -> str:
        return f"https://mock-s3.local/{key}?file={file_name}"

    monkeypatch.setattr("routes._audiobook_helpers.get_s3_client", _mock_get_s3_client)
    monkeypatch.setattr("routes._audiobook_helpers.object_create_presigned_url", _mock_presigned_url)
    monkeypatch.setattr("routes.audiobook.get_s3_client", _mock_get_s3_client, raising=False)
    monkeypatch.setattr("routes.audiobook.object_create_presigned_url", _mock_presigned_url, raising=False)
    yield mock_session


@pytest.fixture(scope="session", autouse=True)
def _prewarm_nltk_data() -> None:
    ensure_nltk_data()
