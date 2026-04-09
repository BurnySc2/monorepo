"""Pytest configuration and shared fixtures.

This module is automatically loaded by pytest (via conftest.py naming).
Fixtures defined here are available to all tests without explicit imports.

Fixtures:
    test_client: FastAPI test client for tests that don't need database.
    test_client_db_reset: FastAPI test client with fresh database tables
        created before each test and dropped after.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from piccolo.table import Table, create_db_tables, drop_db_tables
from piccolo.utils.sync import run_sync

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
