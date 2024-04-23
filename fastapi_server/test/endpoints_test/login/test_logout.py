from test.base_test import test_client  # noqa: F401

import pytest
from litestar.status_codes import HTTP_200_OK
from litestar.testing import TestClient

from routes.login_logout import COOKIES


@pytest.mark.asyncio
async def test_route_github_logout(test_client: TestClient) -> None:  # noqa: F811
    test_client.cookies[COOKIES["github"]] = "valid_access_token"
    response = test_client.get("/logout")
    assert response.status_code == HTTP_200_OK
    assert response.url.path == "/login"
    # TODO Make sure cookie gets deleted - HOW?!
    # assert test_client.cookies.get(COOKIES["github"]) is None


@pytest.mark.asyncio
async def test_route_twitch_logout(test_client: TestClient) -> None:  # noqa: F811
    test_client.cookies[COOKIES["twitch"]] = "valid_access_token"
    response = test_client.get("/logout")
    assert response.status_code == HTTP_200_OK
    assert response.url.path == "/login"
    # TODO Make sure cookie gets deleted - HOW?!
    # assert test_client.cookies.get(COOKIES["twitch"]) is None
