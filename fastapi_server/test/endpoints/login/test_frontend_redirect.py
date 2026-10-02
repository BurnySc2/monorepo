from fastapi import status
from fastapi.testclient import TestClient
from pytest_httpx import HTTPXMock

from components.login.cookies import COOKIES
from settings import settings
from test.conftest import test_client  # noqa: F401

_test_client = test_client


def test_twitch_no_code_redirects_to_frontend_url(test_client: TestClient) -> None:
    response = test_client.get("/login/twitch", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["location"] == settings.frontend_url.rstrip("/")


def test_twitch_already_logged_in_redirects_to_frontend_url(test_client: TestClient, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.twitch.tv/helix/users",
        json={"data": [{"id": "123", "login": "abc", "display_name": "Abc", "email": "abc@example.com"}]},
    )
    test_client.cookies[COOKIES["twitch"]] = "valid_access_token"
    response = test_client.get("/login/twitch", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["location"] == settings.frontend_url.rstrip("/")


def test_twitch_error_redirects_to_frontend_error_url(test_client: TestClient, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://id.twitch.tv/oauth2/token",
        json={"error": "some_error_message"},
    )
    response = test_client.get("/login/twitch?code=mycode", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    expected = settings.frontend_url.rstrip("/") + "/?error=oauth_failed"
    assert response.headers["location"] == expected
    assert "/login?error" not in response.headers["location"]


def test_frontend_url_ignores_host_header(test_client: TestClient) -> None:
    response = test_client.get("/login/twitch", follow_redirects=False, headers={"Host": "evil.com"})
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["location"] == settings.frontend_url.rstrip("/")
    assert "evil.com" not in response.headers["location"]
