import os

import pytest
from dataset import Table  # pyre-fixme[21]
from litestar.testing import TestClient
from pytest_httpx import HTTPXMock

from app import app
from routes.audiobook.schema import db
from routes.login_logout import COOKIES


@pytest.fixture
def test_client():
    # Reset db
    # TODO Doesn't seem to work in memory due to SQLAlchemy
    assert os.getenv("POSTGRES_CONNECTION_STRING") == "sqlite:///test.db"
    with db:
        table_name: str
        for table_name in db.tables:
            table: Table = db[table_name]
            table.drop()

    with TestClient(app=app) as client:
        yield client


def log_in_with_twitch(test_client: TestClient, httpx_mock: HTTPXMock) -> None:
    test_client.cookies[COOKIES["twitch"]] = "valid_access_token"
    httpx_mock.add_response(
        url="https://api.twitch.tv/helix/users",
        json={"data": [{"id": "123", "login": "abc", "display_name": "Abc", "email": "abc@example.com"}]},
    )


# class BaseTest:
#     method_client: TestClient = None

#     def setup_method(self, _method):
#         BaseTest.method_client = TestClient(app)

#     def teardown_method(self, _method):
#         BaseTest.method_client = None

#     @classmethod
#     @contextlib.contextmanager
#     def method_client_context(cls):
#         client = TestClient(app)
#         try:
#             yield client
#         finally:
#             cls.example_client = None

#     @pytest.fixture(name="method_client_fixture")
#     def method_client_fixture(self) -> Generator[TestClient, None, None]:
#         with BaseTest.method_client_context() as client:
#             assert isinstance(client, TestClient)
#             yield client
