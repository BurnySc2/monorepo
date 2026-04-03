import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pytest_httpx import HTTPXMock

from components.login.cookies import COOKIES, LoggedInUser, TwitchUser, twitch_get_user
from components.login.twitch import twitch_verify_code

from test.conftest import test_client  # noqa: F401


_test_client = test_client


@pytest.mark.asyncio
async def test_twitch_get_user_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.twitch.tv/helix/users",
        json={"data": [{"id": "123", "login": "abc", "display_name": "Abc", "email": "abc@example.com"}]},
    )
    result = await twitch_get_user("test_access_token")
    assert result is not None
    assert result.id == 123
    assert result.login == "abc"
    assert result.display_name == "Abc"
    assert result.email == ""


@pytest.mark.asyncio
async def test_twitch_get_user_no_access_token():
    result = await twitch_get_user(None)
    assert result is None


@pytest.mark.asyncio
async def test_twitch_verify_code_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://id.twitch.tv/oauth2/token",
        json={"access_token": "myaccesstoken"},
    )
    result = await twitch_verify_code("mycode")
    assert result == "myaccesstoken"


@pytest.mark.asyncio
async def test_twitch_verify_code_service_down(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://id.twitch.tv/oauth2/token",
        status_code=503,
    )
    result = await twitch_verify_code("mycode")
    assert result == 503


@pytest.mark.asyncio
async def test_twitch_verify_code_error(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://id.twitch.tv/oauth2/token",
        json={"error": "some_error_message"},
    )
    result = await twitch_verify_code("mycode")
    assert result == 409


def test_route_twitch_login_already_logged_in(test_client: TestClient, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.twitch.tv/helix/users",
        json={"data": [{"id": "123", "login": "abc", "display_name": "Abc", "email": "abc@example.com"}]},
    )
    test_client.cookies[COOKIES["twitch"]] = "valid_access_token"
    response = test_client.get("/login/twitch", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert test_client.cookies[COOKIES["twitch"]] == "valid_access_token"


def test_route_twitch_login_no_code_redirects(test_client: TestClient) -> None:
    response = test_client.get("/login/twitch", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT


def test_route_twitch_login_code_given_success(test_client: TestClient, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://id.twitch.tv/oauth2/token",
        json={"access_token": "myaccesstoken"},
    )
    assert COOKIES["twitch"] not in test_client.cookies
    response = test_client.get("/login/twitch?code=mycode", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert test_client.cookies[COOKIES["twitch"]] == "myaccesstoken"


def test_route_twitch_login_code_given_but_service_down(test_client: TestClient, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://id.twitch.tv/oauth2/token",
        status_code=503,
    )
    response = test_client.get("/login/twitch?code=mycode", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert "error=oauth_failed" in response.headers["location"]


def test_route_twitch_login_code_given_but_error(test_client: TestClient, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://id.twitch.tv/oauth2/token",
        json={"error": "some_error_message"},
    )
    response = test_client.get("/login/twitch?code=mycode", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert "error=oauth_failed" in response.headers["location"]


@pytest.mark.asyncio
async def test_twitch_get_user_api_error(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.twitch.tv/helix/users",
        status_code=401,
    )
    result = await twitch_get_user("invalid_token")
    assert result is None


@pytest.mark.asyncio
async def test_twitch_get_user_server_error(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.twitch.tv/helix/users",
        status_code=500,
    )
    result = await twitch_get_user("test_token")
    assert result is None


def test_logged_in_user_from_twitch_user():
    twitch_user = TwitchUser(id=123, login="abc", display_name="Abc", email="abc@example.com")
    result = LoggedInUser.from_service(twitch_user)
    assert result is not None
    assert result.id == 123
    assert result.name == "Abc"
    assert result.service == "twitch"
