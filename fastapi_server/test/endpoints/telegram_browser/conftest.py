from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from piccolo.table import create_db_tables, drop_db_tables
from piccolo.utils.sync import run_sync

from components.login.cookies import LoggedInUser, get_current_user
from main import app
from models.telegram_browser import TelegramChannel, TelegramMessage

TABLES = [TelegramChannel, TelegramMessage]


def _mock_get_current_user() -> LoggedInUser:
    return LoggedInUser(id=1, name="testuser", service="github")


@pytest.fixture(scope="function")
def telegram_client() -> Iterator[TestClient]:
    run_sync(create_db_tables(*TABLES, if_not_exists=True))
    app.dependency_overrides[get_current_user] = _mock_get_current_user
    try:
        with TestClient(app=app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        run_sync(drop_db_tables(*TABLES))
