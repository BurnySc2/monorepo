import os
from pathlib import Path
from test.base_test import log_in_with_twitch, test_client  # noqa: F401

import dataset  # pyre-fixme[21]
import pytest

# import pytest
from bs4 import BeautifulSoup  # pyre-fixme[21]
from litestar.contrib.htmx._utils import HTMXHeaders
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_401_UNAUTHORIZED,
)
from litestar.testing import TestClient
from pytest_httpx import HTTPXMock

_test_client = test_client


def setup_function(function):
    global db
    # Create new database connection on each function call
    db = dataset.connect(os.getenv("POSTGRES_CONNECTION_STRING"))
    # TODO Can't access db directly from test functions, but the server seems to handle it correctly
    # Perhaps adding a test-endpoint to verify that data is in the database?


def test_index_route_inaccessable_when_not_logged_in(test_client: TestClient) -> None:  # noqa: F811
    response = test_client.get("/audiobook/epub_upload")
    assert response.status_code == 401


# Test "/" has upload button
def test_index_route_has_upload_button(test_client: TestClient, httpx_mock: HTTPXMock) -> None:  # noqa: F811
    log_in_with_twitch(test_client, httpx_mock)
    response = test_client.get("/audiobook/epub_upload")
    assert response.status_code == HTTP_200_OK
    # assert button exists with text "Upload"
    soup = BeautifulSoup(response.text, features="lxml")
    assert len(soup.find_all("button", type="submit")) == 1


# Test post request to "/" can upload an epub
@pytest.mark.parametrize(
    "book_relative_path, book_id, chapters_amount",
    [
        ("actual_books/frankenstein.epub", 1, 31),
        ("actual_books/romeo-and-juliet.epub", 2, 28),
        ("actual_books/the-war-of-the-worlds.epub", 3, 29),
    ],
)
def test_index_route_upload_epub(
    book_relative_path: str, book_id: int, chapters_amount: int, test_client: TestClient, httpx_mock: HTTPXMock
) -> None:  # noqa: F811
    log_in_with_twitch(test_client, httpx_mock)

    # Make sure the book does not exist yet
    response = test_client.get(f"/audiobook/book/{book_id}")
    assert response.status_code == HTTP_401_UNAUTHORIZED

    # Upload book
    book_path = Path(__file__).parent / book_relative_path
    response = test_client.post("/audiobook/epub_upload", files={"upload-file": book_path.open("rb")})
    assert response.status_code == HTTP_201_CREATED
    # Why is the database not empty?
    assert response.headers.get(HTMXHeaders.REDIRECT) == f"/audiobook/book/{book_id}"
    assert response.headers.get("location") is None

    # Clean up responses to avoid assertion failure
    httpx_mock.reset(assert_all_responses_were_requested=False)

    # Make sure N chapters were detected
    response2 = test_client.get(response.headers.get(HTMXHeaders.REDIRECT))
    soup = BeautifulSoup(response2.text, features="lxml")
    matching_divs = soup.find_all("div", id=lambda x: x is not None and x.startswith("chapter_audio_"))
    assert response2.status_code == HTTP_200_OK
    assert len(matching_divs) == chapters_amount


# Test post request to "/" book already exists
def test_index_route_upload_epub_twice(test_client: TestClient, httpx_mock: HTTPXMock) -> None:  # noqa: F811
    log_in_with_twitch(test_client, httpx_mock)

    # Make sure the book does not exist yet
    response = test_client.get("/audiobook/book/1")
    # Why is this not 401?
    assert response.status_code == HTTP_200_OK

    # Upload book the first time
    book_path = Path(__file__).parent / "actual_books/frankenstein.epub"
    response2 = test_client.post("/audiobook/epub_upload", files={"upload-file": book_path.open("rb")})
    assert response2.status_code == HTTP_201_CREATED
    assert response2.headers.get(HTMXHeaders.REDIRECT) == "/audiobook/book/1"
    assert response2.headers.get("location") is None

    # Upload a second time
    response3 = test_client.post("/audiobook/epub_upload", files={"upload-file": book_path.open("rb")})
    assert response2.status_code == HTTP_201_CREATED
    # Make sure it points to the same book
    assert response3.headers.get(HTMXHeaders.REDIRECT) == "/audiobook/book/1"
    assert response3.headers.get("location") is None

    # Clean up responses to avoid assertion failure
    httpx_mock.reset(assert_all_responses_were_requested=False)


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
