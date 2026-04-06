from fastapi import status
from fastapi.testclient import TestClient
from pytest_httpx import HTTPXMock

from components.login.cookies import COOKIES
from test.conftest import test_client  # noqa: F401

_test_client = test_client


def test_route_github_login_already_logged_in(test_client: TestClient, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.github.com/user",
        json={"id": 123, "login": "Abc"},
    )
    test_client.cookies[COOKIES["github"]] = "valid_access_token"
    response = test_client.get("/login/github", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert test_client.cookies[COOKIES["github"]] == "valid_access_token"


def test_route_github_login_no_code_redirects(test_client: TestClient) -> None:
    response = test_client.get("/login/github", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT


def test_route_github_login_code_given_success(test_client: TestClient, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://github.com/login/oauth/access_token",
        json={"access_token": "myaccesstoken"},
    )
    assert COOKIES["github"] not in test_client.cookies
    response = test_client.get("/login/github?code=mycode", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert test_client.cookies[COOKIES["github"]] == "myaccesstoken"


def test_route_github_login_code_given_but_error(test_client: TestClient, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://github.com/login/oauth/access_token",
        json={"error": "some_error_message"},
    )
    response = test_client.get("/login/github?code=mycode", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert "error=oauth_failed" in response.headers["location"]


def test_route_start_twitch_login(test_client: TestClient) -> None:
    response = test_client.get("/login/twitch/start", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    location = response.headers["location"]
    assert "https://id.twitch.tv/oauth2/authorize" in location
    assert "client_id=" in location
    assert "redirect_uri=" in location
    assert "response_type=code" in location
    assert "scope=" in location and "user" in location and "email" in location


def test_route_start_github_login(test_client: TestClient) -> None:
    response = test_client.get("/login/github/start", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    location = response.headers["location"]
    assert "https://github.com/login/oauth/authorize" in location
    assert "client_id=" in location
    assert "redirect_uri=" in location
    assert "response_type=code" in location
    assert "scope=read:user" in location or "scope=read%3Auser" in location
