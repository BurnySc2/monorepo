from test.base_test import test_client  # noqa: F401
from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiohttp import ClientSession
from litestar.status_codes import HTTP_200_OK, HTTP_409_CONFLICT, HTTP_503_SERVICE_UNAVAILABLE
from litestar.testing import TestClient

from routes.login_logout import COOKIES, TwitchUser, UserCache, get_twitch_user


@pytest.mark.asyncio
async def test_get_twitch_user_success():
    mock_data = {"data": [{"id": "123", "login": "abc", "display_name": "Abc", "email": "abc@example.com"}]}
    mock_json = AsyncMock(return_value=mock_data)
    mock_get = AsyncMock(return_value=AsyncMock(ok=True, json=mock_json))
    with patch.object(ClientSession, "get", mock_get):
        result = await get_twitch_user("test_access_token")
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


@pytest.mark.asyncio
async def test_route_twitch_login_already_logged_in(test_client: TestClient) -> None:  # noqa: F811
    # User needs to have the twitch cookie to be linked to an account
    test_client.cookies[COOKIES["twitch"]] = "valid_access_token"
    # Get request needs to return the user data
    mock_data = {"data": [{"id": "123", "login": "abc", "display_name": "Abc", "email": "abc@example.com"}]}
    mock_json = AsyncMock(return_value=mock_data)
    mock_get = AsyncMock(return_value=AsyncMock(ok=True, json=mock_json))
    with patch.object(ClientSession, "get", mock_get):  # noqa: SIM117
        response = test_client.get("/login/twitch")
        assert response.status_code == HTTP_200_OK
        assert response.url.path == "/login"
        # Make sure cookie remains unchanged
        assert test_client.cookies[COOKIES["twitch"]] == "valid_access_token"


@pytest.mark.asyncio
async def test_route_twitch_login_code_given_success(test_client: TestClient) -> None:  # noqa: F811
    """
    This test case checks the behavior of the application when the Twitch API returns the access token
    successfully using a code.
    """
    # Post request needs to return the access token
    mock_data = {"access_token": "myaccesstoken"}
    mock_json = AsyncMock(return_value=mock_data)
    mock_post = AsyncMock(return_value=AsyncMock(ok=True, json=mock_json))
    with patch.object(ClientSession, "post", mock_post):  # noqa: SIM117
        # Make sure cookie was not set before
        assert COOKIES["twitch"] not in test_client.cookies
        # Twitch api returns a parameter "code=somevalue" which can be used to fetch the access token
        response = test_client.get("/login/twitch?code=mycode")
        assert response.status_code == HTTP_200_OK
        assert response.url.path == "/login"
        # Make sure cookie has been set
        assert test_client.cookies[COOKIES["twitch"]] == "myaccesstoken"


@pytest.mark.asyncio
async def test_route_twitch_login_code_given_but_service_down(test_client: TestClient) -> None:  # noqa: F811
    """
    This test case checks the behavior of the application when the Twitch API is down
    while trying to fetch the access token using a code.
    """
    mock_post = AsyncMock(return_value=AsyncMock(ok=False))
    with patch.object(ClientSession, "post", mock_post):  # noqa: SIM117
        response = test_client.get("/login/twitch?code=mycode")
        assert response.status_code == HTTP_503_SERVICE_UNAVAILABLE


@pytest.mark.asyncio
async def test_route_twitch_login_code_given_but_error(test_client: TestClient) -> None:  # noqa: F811
    """
    This test case checks the behavior of the application when the Twitch API returns an error
    while trying to fetch the access token using a code.
    """
    mock_data = {"error": "some_error_message"}
    mock_json = AsyncMock(return_value=mock_data)
    mock_post = AsyncMock(return_value=AsyncMock(ok=True, json=mock_json))
    with patch.object(ClientSession, "post", mock_post):  # noqa: SIM117
        response = test_client.get("/login/twitch?code=mycode")
        assert response.status_code == HTTP_409_CONFLICT


# TODO same for github in other file
