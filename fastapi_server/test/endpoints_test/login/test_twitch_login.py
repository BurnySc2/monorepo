from test.base_test import test_client  # noqa: F401  # noqa: F401
from unittest.mock import Mock, patch

import pytest
from litestar.contrib.htmx._utils import HTMXHeaders
from litestar.status_codes import HTTP_200_OK, HTTP_409_CONFLICT, HTTP_503_SERVICE_UNAVAILABLE
from litestar.testing import TestClient
from pytest_httpx import HTTPXMock

from routes.login_logout import COOKIES, TwitchUser, UserCache, get_twitch_user

_test_client = test_client


@pytest.mark.asyncio
async def test_get_twitch_user_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.twitch.tv/helix/users",
        json={"data": [{"id": "123", "login": "abc", "display_name": "Abc", "email": "abc@example.com"}]},
    )
    result = await get_twitch_user("test_access_token")
    assert result is not None
    assert result.id == 123
    assert result.login == "abc"
    assert result.display_name == "Abc"
    assert result.email == ""


@pytest.mark.asyncio
async def test_get_twitch_user_from_cache():
    mock_user = TwitchUser(id=123, login="abc", display_name="Abc", email="")
    mock_get = Mock(return_value=mock_user)
    with patch.object(UserCache, "__getitem__", mock_get):
        result = await get_twitch_user("test_access_token")
        assert result.id == 123
        assert result.login == "abc"
        assert result.display_name == "Abc"
        assert result.email == ""


@pytest.mark.asyncio
async def test_get_twitch_user_no_access_token():
    result = await get_twitch_user()
    assert result is None


def test_route_twitch_login_already_logged_in(test_client: TestClient, httpx_mock: HTTPXMock) -> None:  # noqa: F811
    # User needs to have the twitch cookie to be linked to an account
    test_client.cookies[COOKIES["twitch"]] = "valid_access_token"
    # Get request needs to return the user data
    response = test_client.get("/login/twitch")
    assert response.status_code == HTTP_200_OK
    assert response.headers.get(HTMXHeaders.REDIRECT) == "/login"
    assert response.headers.get("location") is None
    # Make sure cookie remains unchanged
    assert test_client.cookies[COOKIES["twitch"]] == "valid_access_token"


def test_route_twitch_login_code_given_success(test_client: TestClient, httpx_mock: HTTPXMock) -> None:  # noqa: F811
    """
    This test case checks the behavior of the application when the Twitch API returns the access token
    successfully using a code.
    """
    # Post request needs to return the access token
    httpx_mock.add_response(
        url="https://id.twitch.tv/oauth2/token",
        json={"access_token": "myaccesstoken"},
    )
    # Make sure cookie was not set before
    assert COOKIES["twitch"] not in test_client.cookies
    # Twitch api returns a parameter "code=somevalue" which can be used to fetch the access token
    response = test_client.get("/login/twitch?code=mycode")
    assert response.status_code == HTTP_200_OK
    assert response.headers.get(HTMXHeaders.REDIRECT) == "/login"
    assert response.headers.get("location") is None
    # Make sure cookie has been set
    assert test_client.cookies[COOKIES["twitch"]] == "myaccesstoken"


def test_route_twitch_login_code_given_but_service_down(test_client: TestClient, httpx_mock: HTTPXMock) -> None:  # noqa: F811
    """
    This test case checks the behavior of the application when the Twitch API is down
    while trying to fetch the access token using a code.
    """
    httpx_mock.add_response(url="https://id.twitch.tv/oauth2/token", status_code=501)
    response = test_client.get("/login/twitch?code=mycode")
    assert response.status_code == HTTP_503_SERVICE_UNAVAILABLE


def test_route_twitch_login_code_given_but_error(test_client: TestClient, httpx_mock: HTTPXMock) -> None:  # noqa: F811
    """
    This test case checks the behavior of the application when the Twitch API returns an error
    while trying to fetch the access token using a code.
    """
    httpx_mock.add_response(
        url="https://id.twitch.tv/oauth2/token",
        json={"error": "some_error_message"},
    )
    response = test_client.get("/login/twitch?code=mycode")
    assert response.status_code == HTTP_409_CONFLICT
