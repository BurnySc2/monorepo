from unittest.mock import AsyncMock, patch

import pytest
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_409_CONFLICT,
    HTTP_503_SERVICE_UNAVAILABLE,
)
from litestar.stores.memory import MemoryStore
from litestar.testing import TestClient
from pytest_httpx import HTTPXMock

from src.routes.caches import global_cache
from src.routes.cookies_and_guards import (
    COOKIES,
    GithubUser,
    provide_github_user,
)
from test.base_test import test_client  # noqa: F401

_test_client = test_client


@pytest.mark.asyncio
async def test_get_github_user_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.github.com/user",
        json={"id": 123, "login": "Abc"},
    )
    result = await provide_github_user("test_access_token")
    assert result is not None
    assert result.id == 123
    assert result.login == "Abc"


@pytest.mark.asyncio
async def test_get_github_user_from_cache():
    mock_user = GithubUser(id=123, login="Abc")
    mock_get = AsyncMock(return_value=mock_user)
    with patch.object(MemoryStore, "get", mock_get):
        result = await provide_github_user("test_access_token")
        assert result is not None
        assert result.id == 123
        assert result.login == "Abc"


@pytest.mark.asyncio
async def test_get_github_user_no_access_token():
    result = await provide_github_user()
    assert result is None


@pytest.mark.asyncio
async def test_route_github_login_already_logged_in(test_client: TestClient, httpx_mock: HTTPXMock) -> None:  # noqa: F811
    await global_cache.delete_all()
    # User needs to have the github cookie to be linked to an account
    test_client.cookies[COOKIES["github"]] = "valid_access_token"
    # Get request needs to return the user data
    httpx_mock.add_response(
        url="https://api.github.com/user",
        json={"id": 123, "login": "Abc"},
    )
    response = test_client.get("/login/github")
    assert response.status_code == HTTP_200_OK
    assert response.url.path == "/login"
    # Make sure cookie remains unchanged
    assert test_client.cookies[COOKIES["github"]] == "valid_access_token"


def test_route_github_login_code_given_success(test_client: TestClient, httpx_mock: HTTPXMock) -> None:  # noqa: F811
    """
    This test case checks the behavior of the application when the Github API returns the access token
    successfully using a code.
    """
    # Post request needs to return the access token
    httpx_mock.add_response(
        url="https://github.com/login/oauth/access_token",
        json={"access_token": "myaccesstoken"},
    )
    # Make sure the user can log in with access token afterwards
    httpx_mock.add_response(
        url="https://api.github.com/user",
        json={"id": 123, "login": "Abc"},
    )
    # Make sure cookie was not set before
    assert COOKIES["github"] not in test_client.cookies
    # Github api returns a parameter "code=somevalue" which can be used to fetch the access token
    response = test_client.get("/login/github?code=mycode")
    assert response.status_code == HTTP_200_OK
    assert response.url.path == "/login"
    # Make sure cookie has been set
    assert test_client.cookies[COOKIES["github"]] == "myaccesstoken"


def test_route_github_login_code_given_but_service_down(test_client: TestClient, httpx_mock: HTTPXMock) -> None:  # noqa: F811
    """
    This test case checks the behavior of the application when the Github API is down
    while trying to fetch the access token using a code.
    """
    httpx_mock.add_response(
        url="https://github.com/login/oauth/access_token",
        status_code=503,
    )
    response = test_client.get("/login/github?code=mycode")
    assert response.status_code == HTTP_503_SERVICE_UNAVAILABLE


def test_route_github_login_code_given_but_error(test_client: TestClient, httpx_mock: HTTPXMock) -> None:  # noqa: F811
    """
    This test case checks the behavior of the application when the Github API returns an error
    while trying to fetch the access token using a code.
    """
    httpx_mock.add_response(
        url="https://github.com/login/oauth/access_token",
        json={"error": "some_error_message"},
    )
    response = test_client.get("/login/github?code=mycode")
    assert response.status_code == HTTP_409_CONFLICT
