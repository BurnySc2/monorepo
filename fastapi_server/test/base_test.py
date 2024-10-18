from collections.abc import Iterator

import pytest
from litestar import Litestar
from litestar.testing import TestClient
from pytest_httpx import HTTPXMock

from prisma.cli import prisma
from src.app import app
from src.routes.login_logout import COOKIES


# TODO Use one fixture that resets db and another that doesnt
@pytest.fixture(scope="function")
def test_client() -> Iterator[TestClient[Litestar]]:
    with TestClient(app=app, raise_server_exceptions=True) as client:
        yield client


@pytest.fixture(scope="function")
def test_client_db_reset() -> Iterator[TestClient[Litestar]]:
    prisma.run(["db", "push", "--force-reset"], check=True)
    with TestClient(app=app, raise_server_exceptions=True) as client:
        yield client


def log_in_with_twitch(test_client: TestClient, httpx_mock: HTTPXMock) -> None:
    test_client.cookies[COOKIES["twitch"]] = "valid_access_token"
    httpx_mock.add_response(
        url="https://api.twitch.tv/helix/users",
        json={"data": [{"id": "123", "login": "abc", "display_name": "Abc", "email": "abc@example.com"}]},
    )


# TODO Login with github and google

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
