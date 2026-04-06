from fastapi import status
from fastapi.testclient import TestClient
from pytest_httpx import HTTPXMock

from components.login.cookies import COOKIES
from test.conftest import test_client  # noqa: F401

_test_client = test_client


def test_route_login_status_not_logged_in(test_client: TestClient) -> None:
    response = test_client.get("/login")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"logged_in": False}


def test_route_login_status_github_logged_in(test_client: TestClient, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.github.com/user",
        json={"id": 123, "login": "Abc"},
    )
    test_client.cookies[COOKIES["github"]] = "valid_access_token"
    response = test_client.get("/login")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["logged_in"] is True
    assert data["user"]["id"] == 123
    assert data["user"]["name"] == "Abc"
    assert data["user"]["service"] == "github"


def test_route_login_status_twitch_logged_in(test_client: TestClient, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.twitch.tv/helix/users",
        json={"data": [{"id": "456", "login": "xyz", "display_name": "Xyz", "email": "xyz@example.com"}]},
    )
    test_client.cookies[COOKIES["twitch"]] = "valid_access_token"
    response = test_client.get("/login")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["logged_in"] is True
    assert data["user"]["id"] == 456
    assert data["user"]["name"] == "Xyz"
    assert data["user"]["service"] == "twitch"


def test_route_google_login_callback(test_client: TestClient) -> None:
    response = test_client.get("/login/google", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["location"] is not None
