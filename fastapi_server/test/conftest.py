"""Pytest configuration and shared fixtures.

This module is automatically loaded by pytest (via conftest.py naming).
Fixtures defined here are available to all tests without explicit imports.

Fixtures:
    test_client: FastAPI test client for tests that don't need database.
    test_client_db_reset: FastAPI test client with fresh database tables
        created before each test and dropped after.
"""

from collections.abc import Iterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from piccolo.table import Table, create_db_tables, drop_db_tables
from piccolo.utils.sync import run_sync

from components.audiobook.epub_reader import _ensure_nltk_data
from components.login.cookies import LoggedInUser, get_current_user
from main import app
from schemas.audiobook.db_models import AudiobookBook, AudiobookChapter

TABLES: list[type[Table]] = [AudiobookBook, AudiobookChapter]


@pytest.fixture(scope="function")
def test_client() -> Iterator[TestClient]:
    with TestClient(app=app) as client:
        yield client


def _mock_get_current_user() -> LoggedInUser:
    return LoggedInUser(id=1, name="testuser", service="github")


@pytest.fixture(scope="function")
def test_client_db_reset() -> Iterator[TestClient]:
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
    _ensure_nltk_data()
