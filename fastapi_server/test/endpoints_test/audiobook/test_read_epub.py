from test.base_test import test_client  # noqa: F401

import pytest
from bs4 import BeautifulSoup
from litestar.status_codes import HTTP_200_OK
from litestar.testing import TestClient
from pytest_httpx import HTTPXMock

from routes.login_logout import COOKIES

_test_client = test_client


@pytest.mark.asyncio
async def test_index_route_inaccessable_when_not_logged_in(test_client: TestClient) -> None:  # noqa: F811
    response = test_client.get("/twitch/audiobook/epub")
    assert response.status_code == 401


# Test "/" has upload button
@pytest.mark.asyncio
async def test_index_route_has_upload_button(test_client: TestClient, httpx_mock: HTTPXMock) -> None:  # noqa: F811
    test_client.cookies[COOKIES["twitch"]] = "valid_access_token"
    httpx_mock.add_response(
        url="https://api.twitch.tv/helix/users",
        json={"data": [{"id": "123", "login": "abc", "display_name": "Abc", "email": "abc@example.com"}]},
    )
    response = test_client.get("/twitch/audiobook/epub")
    assert response.status_code == HTTP_200_OK
    # assert button exists with text "Upload"
    soup = BeautifulSoup(response.text, features="lxml")
    assert len(soup.find_all("button", type="submit", string="Upload")) == 1


# Test post request to "/" can upload an epub

# Test "/book/book_id" has an uploaded book

# Test "/generate_audio" can generate audio for a chapter
# Test "/load_generated_audio" loads an audio file
# Test "/download_chapter_mp3" allows download of a chapter
# Test "/generate_audio_book" queues the full book to be converted
# Test "/download_book_zip" downloads a zip file
# Test "/delete_book" deletes the book and all chapters
# Test "/delete_generated_audio" deletes a chapter
# Test "/save_settings_to_cookies" sets cookies
