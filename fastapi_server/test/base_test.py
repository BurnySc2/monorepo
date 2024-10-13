import pytest
from litestar.testing import TestClient
from pytest_httpx import HTTPXMock

from src.app import app
from src.routes.login_logout import COOKIES


@pytest.fixture
def test_client():
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
