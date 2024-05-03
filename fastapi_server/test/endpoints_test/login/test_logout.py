from test.base_test import test_client  # noqa: F401

from litestar.contrib.htmx._utils import HTMXHeaders
from litestar.status_codes import HTTP_302_FOUND
from litestar.testing import TestClient

from routes.login_logout import COOKIES

_test_client = test_client


def test_route_github_logout(test_client: TestClient) -> None:  # noqa: F811
    test_client.cookies[COOKIES["github"]] = "valid_access_token"
    response = test_client.get("/logout")
    assert response.status_code == HTTP_302_FOUND
    assert response.headers.get(HTMXHeaders.REDIRECT) == "/login"
    assert response.headers.get("location") is None
    # TODO Make sure cookie gets deleted - HOW?!
    # assert test_client.cookies.get(COOKIES["github"]) is None


def test_route_twitch_logout(test_client: TestClient) -> None:  # noqa: F811
    test_client.cookies[COOKIES["twitch"]] = "valid_access_token"
    response = test_client.get("/logout")
    assert response.status_code == HTTP_302_FOUND
    assert response.headers.get(HTMXHeaders.REDIRECT) == "/login"
    assert response.headers.get("location") is None
    # TODO Make sure cookie gets deleted - HOW?!
    # assert test_client.cookies.get(COOKIES["twitch"]) is None
