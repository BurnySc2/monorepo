from test.base_test import test_client  # noqa: F401
from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiohttp import ClientSession
from litestar.status_codes import HTTP_200_OK, HTTP_409_CONFLICT, HTTP_503_SERVICE_UNAVAILABLE
from litestar.testing import TestClient

from routes.login_logout import COOKIES, GithubUser, UserCache, get_github_user


@pytest.mark.asyncio
async def test_get_github_user_success():
    mock_data = {"id": 123, "login": "Abc"}
    mock_json = AsyncMock(return_value=mock_data)
    mock_get = AsyncMock(return_value=AsyncMock(ok=True, json=mock_json))
    with patch.object(ClientSession, "get", mock_get):
        result = await get_github_user("test_access_token")
        assert result.id == 123
        assert result.login == "Abc"


@pytest.mark.asyncio
async def test_get_github_user_from_cache():
    mock_user = GithubUser(id=123, login="Abc")
    mock_get = Mock(return_value=mock_user)
    with patch.object(UserCache, "__getitem__", mock_get):
        result = await get_github_user("test_access_token")
        assert result.id == 123
        assert result.login == "Abc"


@pytest.mark.asyncio
async def test_get_github_user_no_access_token():
    result = await get_github_user()
    assert result is None


@pytest.mark.asyncio
async def test_route_github_login_already_logged_in(test_client: TestClient) -> None:  # noqa: F811
    # User needs to have the github cookie to be linked to an account
    test_client.cookies[COOKIES["github"]] = "valid_access_token"
    # Get request needs to return the user data
    mock_data = {"id": "123", "login": "Abc"}
    mock_json = AsyncMock(return_value=mock_data)
    mock_get = AsyncMock(return_value=AsyncMock(ok=True, json=mock_json))
    with patch.object(ClientSession, "get", mock_get):  # noqa: SIM117
        response = test_client.get("/login/github")
        assert response.status_code == HTTP_200_OK
        assert response.url.path == "/login"
        # Make sure cookie remains unchanged
        assert test_client.cookies[COOKIES["github"]] == "valid_access_token"


@pytest.mark.asyncio
async def test_route_github_login_code_given_success(test_client: TestClient) -> None:  # noqa: F811
    """
    This test case checks the behavior of the application when the Github API returns the access token
    successfully using a code.
    """
    # Post request needs to return the access token
    mock_data = {"access_token": "myaccesstoken"}
    mock_json = AsyncMock(return_value=mock_data)
    mock_post = AsyncMock(return_value=AsyncMock(ok=True, json=mock_json))
    with patch.object(ClientSession, "post", mock_post):  # noqa: SIM117
        # Make sure cookie was not set before
        assert COOKIES["github"] not in test_client.cookies
        # Github api returns a parameter "code=somevalue" which can be used to fetch the access token
        response = test_client.get("/login/github?code=mycode")
        assert response.status_code == HTTP_200_OK
        assert response.url.path == "/login"
        # Make sure cookie has been set
        assert test_client.cookies[COOKIES["github"]] == "myaccesstoken"


@pytest.mark.asyncio
async def test_route_github_login_code_given_but_service_down(test_client: TestClient) -> None:  # noqa: F811
    """
    This test case checks the behavior of the application when the Github API is down
    while trying to fetch the access token using a code.
    """
    mock_post = AsyncMock(return_value=AsyncMock(ok=False))
    with patch.object(ClientSession, "post", mock_post):  # noqa: SIM117
        response = test_client.get("/login/github?code=mycode")
        assert response.status_code == HTTP_503_SERVICE_UNAVAILABLE


@pytest.mark.asyncio
async def test_route_github_login_code_given_but_error(test_client: TestClient) -> None:  # noqa: F811
    """
    This test case checks the behavior of the application when the Github API returns an error
    while trying to fetch the access token using a code.
    """
    mock_data = {"error": "some_error_message"}
    mock_json = AsyncMock(return_value=mock_data)
    mock_post = AsyncMock(return_value=AsyncMock(ok=True, json=mock_json))
    with patch.object(ClientSession, "post", mock_post):  # noqa: SIM117
        response = test_client.get("/login/github?code=mycode")
        assert response.status_code == HTTP_409_CONFLICT
