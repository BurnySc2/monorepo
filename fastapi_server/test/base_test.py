import os
from collections.abc import Iterator

import pytest
from litestar import Litestar
from litestar.testing import TestClient
from minio import Minio
from pytest_httpx import HTTPXMock

from prisma.cli import prisma
from src.app import app
from src.routes.login_logout import COOKIES


@pytest.fixture(scope="function")
def test_client() -> Iterator[TestClient[Litestar]]:
    # Use this client only if the test does not access the test-database
    with TestClient(app=app, raise_server_exceptions=True) as client:
        yield client


@pytest.fixture(scope="function")
def test_client_db_reset() -> Iterator[TestClient[Litestar]]:
    # Use this client if the test accesses and modifies the test-database
    prisma.run(["migrate", "reset", "--force", "--skip-generate"], check=True)
    with TestClient(app=app, raise_server_exceptions=True) as client:
        yield client


@pytest.fixture(scope="function")
def test_minio_client() -> Iterator[Minio]:
    minio_client = Minio(
        os.getenv("MINIO_URL"),
        os.getenv("MINIO_ACCESS_TOKEN"),
        os.getenv("MINIO_SECRET_KEY"),
        secure=False,
    )
    yield minio_client


def log_in_with_twitch(test_client: TestClient, httpx_mock: HTTPXMock) -> None:
    test_client.cookies[COOKIES["twitch"]] = "valid_access_token"
    httpx_mock.add_response(
        url="https://api.twitch.tv/helix/users",
        json={"data": [{"id": "123", "login": "abc", "display_name": "Abc", "email": "abc@example.com"}]},
    )


# TODO Add Logout function and test?

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
