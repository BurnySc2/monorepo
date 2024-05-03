from pathlib import Path
from test.base_test import log_in_with_twitch, test_client  # noqa: F401

from bs4 import BeautifulSoup
from litestar.contrib.htmx._utils import HTMXHeaders
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_201_CREATED,
)
from litestar.testing import TestClient
from pytest_httpx import HTTPXMock

_test_client = test_client


def test_index_route_inaccessable_when_not_logged_in(test_client: TestClient) -> None:  # noqa: F811
    response = test_client.get("/twitch/audiobook/epub")
    assert response.status_code == 401


# Test "/" has upload button
def test_index_route_has_upload_button(test_client: TestClient, httpx_mock: HTTPXMock) -> None:  # noqa: F811
    log_in_with_twitch(test_client, httpx_mock)
    response = test_client.get("/twitch/audiobook/epub")
    assert response.status_code == HTTP_200_OK
    # assert button exists with text "Upload"
    soup = BeautifulSoup(response.text, features="lxml")
    assert len(soup.find_all("button", type="submit", string="Upload")) == 1


# Test post request to "/" can upload an epub
def test_index_route_upload_epub(test_client: TestClient, httpx_mock: HTTPXMock) -> None:  # noqa: F811
    log_in_with_twitch(test_client, httpx_mock)
    book_path = Path(__file__).parent / "actual_books/Frankenstein.epub"
    response = test_client.post(
        "/twitch/audiobook/epub", files={"upload-file": book_path.open("rb")}, follow_redirects=True
    )
    assert response.status_code == HTTP_201_CREATED
    assert response.headers.get(HTMXHeaders.REDIRECT) == "/twitch/audiobook/epub/book/1"
    assert response.headers.get("location") is None
    # Clean up responses to avoid assertion failure
    httpx_mock.reset(assert_all_responses_were_requested=False)


# Test post request to "/" book already exists

# Test "/book/book_id" does not have an uploaded book
# Test "/book/book_id" has an uploaded book
# Test "/generate_audio" can generate audio for a chapter
# Test "/load_generated_audio" loads an audio file
# Test "/download_chapter_mp3" allows download of a chapter
# Test "/generate_audio_book" queues the full book to be converted
# Test "/download_book_zip" downloads a zip file
# Test "/delete_book" deletes the book and all chapters
# Test "/delete_generated_audio" deletes a chapter
# Test "/save_settings_to_cookies" sets cookies
