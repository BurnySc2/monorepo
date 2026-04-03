import pytest
from pytest_httpx import HTTPXMock

from components.login.cookies import GithubUser, LoggedInUser, github_get_user
from components.login.github import github_verify_code


@pytest.mark.asyncio
async def test_github_verify_code_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://github.com/login/oauth/access_token",
        json={"access_token": "myaccesstoken"},
    )
    result = await github_verify_code("testcode")
    assert result == "myaccesstoken"


@pytest.mark.asyncio
async def test_github_verify_code_service_down(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://github.com/login/oauth/access_token",
        status_code=503,
    )
    result = await github_verify_code("testcode")
    assert result == 503


@pytest.mark.asyncio
async def test_github_verify_code_error_response(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://github.com/login/oauth/access_token",
        json={"error": "some_error_message"},
    )
    result = await github_verify_code("testcode")
    assert result == 409


@pytest.mark.asyncio
async def test_github_get_user_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.github.com/user",
        json={"id": 123, "login": "Abc"},
    )
    result = await github_get_user("test_access_token")
    assert result is not None
    assert result.id == 123
    assert result.login == "Abc"


@pytest.mark.asyncio
async def test_github_get_user_no_access_token():
    result = await github_get_user(None)
    assert result is None


@pytest.mark.asyncio
async def test_github_get_user_api_error(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.github.com/user",
        status_code=401,
    )
    result = await github_get_user("invalid_token")
    assert result is None


@pytest.mark.asyncio
async def test_github_get_user_server_error(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.github.com/user",
        status_code=500,
    )
    result = await github_get_user("test_token")
    assert result is None


def test_logged_in_user_from_github_user():
    github_user = GithubUser(id=123, login="Abc")
    result = LoggedInUser.from_service(github_user)
    assert result is not None
    assert result.id == 123
    assert result.name == "Abc"
    assert result.service == "github"


def test_logged_in_user_from_none():
    result = LoggedInUser.from_service(None)
    assert result is None
