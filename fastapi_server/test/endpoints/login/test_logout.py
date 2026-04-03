from fastapi import status
from fastapi.testclient import TestClient

from components.login.cookies import COOKIES

from test.conftest import test_client  # noqa: F401


_test_client = test_client


def test_route_github_logout(test_client: TestClient) -> None:
    test_client.cookies[COOKIES["github"]] = "valid_access_token"
    response = test_client.get("/logout", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert "Set-Cookie" in response.headers
    assert COOKIES["github"] in response.headers["Set-Cookie"]
    assert "Max-Age=0" in response.headers["Set-Cookie"]


def test_route_twitch_logout(test_client: TestClient) -> None:
    test_client.cookies[COOKIES["twitch"]] = "valid_access_token"
    response = test_client.get("/logout", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert "Set-Cookie" in response.headers
    assert COOKIES["twitch"] in response.headers["Set-Cookie"]
    assert "Max-Age=0" in response.headers["Set-Cookie"]
