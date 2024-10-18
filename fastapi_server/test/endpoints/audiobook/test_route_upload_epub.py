import io
import re
from pathlib import Path
from test.base_test import log_in_with_twitch, test_client, test_client_db_reset  # noqa: F401
from unittest.mock import AsyncMock, patch

import pytest
from bs4 import BeautifulSoup  # pyre-fixme[21]
from litestar.contrib.htmx._utils import HTMXHeaders
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED
from litestar.testing import TestClient
from pytest_httpx import HTTPXMock

from prisma import Prisma
from src.routes.cookies_and_guards import twitch_cache
from src.workers import convert_audiobook
from src.workers.convert_audiobook import convert_one

_test_client = test_client
_test_client_db_reset = test_client_db_reset


def test_index_route_inaccessable_when_not_logged_in(test_client: TestClient) -> None:  # noqa: F811
    response = test_client.get("/audiobook/epub_upload")
    assert response.status_code == HTTP_401_UNAUTHORIZED


# Test "/" has upload button
def test_index_route_has_upload_button(test_client_db_reset: TestClient, httpx_mock: HTTPXMock) -> None:  # noqa: F811
    log_in_with_twitch(test_client_db_reset, httpx_mock)
    response = test_client_db_reset.get("/audiobook/epub_upload")
    assert response.status_code == HTTP_200_OK
    # assert button exists with text "Upload"
    soup = BeautifulSoup(response.text, features="lxml")
    assert len(soup.find_all("button", type="submit")) == 1


# Test post request to "/" can upload an epub
@pytest.mark.parametrize(
    "book_relative_path, book_id, chapters_amount",
    [
        ("actual_books/frankenstein.epub", 1, 31),
        ("actual_books/romeo-and-juliet.epub", 1, 28),
        ("actual_books/the-war-of-the-worlds.epub", 1, 29),
    ],
)
@pytest.mark.httpx_mock(non_mocked_hosts=["localhost"])
@pytest.mark.asyncio
async def test_index_route_upload_epub(
    book_relative_path: str, book_id: int, chapters_amount: int, test_client_db_reset: TestClient, httpx_mock: HTTPXMock
) -> None:  # noqa: F811
    await twitch_cache.delete_all()
    log_in_with_twitch(test_client_db_reset, httpx_mock)

    # Make sure the book does not exist yet
    response = test_client_db_reset.get(f"/audiobook/book/{book_id}")
    assert response.status_code == HTTP_401_UNAUTHORIZED

    # Upload book
    book_path = Path(__file__).parent / book_relative_path
    response = test_client_db_reset.post("/audiobook/epub_upload", files={"upload-file": book_path.open("rb")})
    assert response.status_code == HTTP_201_CREATED
    # Why is the database not empty?
    assert response.headers.get(HTMXHeaders.REDIRECT) == f"/audiobook/book/{book_id}"
    assert response.headers.get("location") is None

    # Make sure N chapters were detected
    response2 = test_client_db_reset.get(response.headers.get(HTMXHeaders.REDIRECT))
    soup = BeautifulSoup(response2.text, features="lxml")
    matching_divs = soup.find_all("div", id=lambda x: x is not None and x.startswith("chapter_audio_"))
    assert response2.status_code == HTTP_200_OK
    assert len(matching_divs) == chapters_amount


# Test post request to "/" book already exists
@pytest.mark.httpx_mock(non_mocked_hosts=["localhost"])
@pytest.mark.asyncio
async def test_index_route_upload_epub_twice(test_client_db_reset: TestClient, httpx_mock: HTTPXMock) -> None:  # noqa: F811
    await twitch_cache.delete_all()
    log_in_with_twitch(test_client_db_reset, httpx_mock)

    # Make sure the book does not exist yet
    response = test_client_db_reset.get("/audiobook/book/1")
    assert response.status_code == HTTP_401_UNAUTHORIZED

    # Upload book the first time
    book_path = Path(__file__).parent / "actual_books/frankenstein.epub"
    response2 = test_client_db_reset.post("/audiobook/epub_upload", files={"upload-file": book_path.open("rb")})
    assert response2.status_code == HTTP_201_CREATED
    assert response2.headers.get(HTMXHeaders.REDIRECT) == "/audiobook/book/1"
    assert response2.headers.get("location") is None

    # Upload a second time
    response3 = test_client_db_reset.post("/audiobook/epub_upload", files={"upload-file": book_path.open("rb")})
    assert response2.status_code == HTTP_201_CREATED
    # Make sure it points to the same book
    assert response3.headers.get(HTMXHeaders.REDIRECT) == "/audiobook/book/1"
    assert response3.headers.get("location") is None




# Test "/generate_audio" can generate audio for a chapter
@pytest.mark.httpx_mock(non_mocked_hosts=["localhost"])
@pytest.mark.asyncio
async def test_generate_audio_for_chapter(test_client_db_reset: TestClient, httpx_mock: HTTPXMock) -> None:  # noqa: F811
    await twitch_cache.delete_all()
    log_in_with_twitch(test_client_db_reset, httpx_mock)

    # Upload book
    expected_chapter_count = 31
    book_path = Path(__file__).parent / "actual_books/frankenstein.epub"
    upload_book_response = test_client_db_reset.post(
        "/audiobook/epub_upload", files={"upload-file": book_path.open("rb")}
    )
    assert upload_book_response.status_code == HTTP_201_CREATED
    # TODO Check redirect content

    # Make sure expected chapter count was detected
    book_after_upload_response = test_client_db_reset.get("/audiobook/book/1")
    assert book_after_upload_response.status_code == HTTP_200_OK
    book_after_upload_response_soup = BeautifulSoup(book_after_upload_response.text, features="lxml")
    chapters_elements = book_after_upload_response_soup.find_all("div", id=re.compile(r"chapter_audio_\d+"))
    assert len(chapters_elements) == expected_chapter_count
    generate_audio_buttons = book_after_upload_response_soup.find_all(
        lambda tag: tag.name == "button" and tag.text.strip() == "Generate audio"
    )
    assert len(generate_audio_buttons) == expected_chapter_count

    # Request to generate audio for first chapter
    click_generate_audio_response = test_client_db_reset.post(
        "/audiobook/generate_audio",
        params={
            "book_id": 1,
            "chapter_number": 1,
        },
    )
    assert click_generate_audio_response.status_code == HTTP_200_OK
    # Text "Queued" will be in the response html element
    click_generate_audio_response_soup = BeautifulSoup(click_generate_audio_response.text, features="lxml")
    assert "Queued" in click_generate_audio_response_soup.text

    # Check how many chapters are available after clicking generate audio
    book_after_generate_audio_response = test_client_db_reset.get("/audiobook/book/1")
    assert book_after_generate_audio_response.status_code == HTTP_200_OK
    book_after_generate_audio_response_soup = BeautifulSoup(book_after_generate_audio_response.text, features="lxml")
    generate_audio_buttons_after_clicking_generate = book_after_generate_audio_response_soup.find_all(
        lambda tag: tag.name == "button" and tag.text.strip() == "Generate audio"
    )
    assert len(generate_audio_buttons_after_clicking_generate) == expected_chapter_count - 1

    example_audio_bytes = b"asd_my_audio"
    with patch.object(
        convert_audiobook,
        "generate_text_to_speech",
        new=AsyncMock(
            # Audio bytes
            return_value=io.BytesIO(example_audio_bytes),
        ),
    ):
        # Convert one chapter to audio, save it in db and in minio
        await convert_one()

    # Audio has been generated, a different HTML element will be returned which allows loading audio
    load_audio_response = test_client_db_reset.post(
        "/audiobook/generate_audio",
        params={
            "book_id": 1,
            "chapter_number": 1,
        },
    )
    assert load_audio_response.status_code == HTTP_200_OK
    # Text "Load audio" will be in the response
    load_audio_response_soup = BeautifulSoup(load_audio_response.text, features="lxml")
    assert "Load audio" in load_audio_response_soup.text

    # Make sure one element with "Load audio" button exists
    book_after_audio_was_generated_response = test_client_db_reset.get("/audiobook/book/1")
    assert book_after_audio_was_generated_response.status_code == HTTP_200_OK
    book_after_audio_was_generated_response_soup = BeautifulSoup(
        book_after_audio_was_generated_response.text, features="lxml"
    )
    generate_audio_buttons_after_clicking_generate = book_after_audio_was_generated_response_soup.find_all(
        lambda tag: tag.name == "button" and "Load audio" in tag.text
    )
    assert len(generate_audio_buttons_after_clicking_generate) == 1

    # Issue loading the <audio> element
    load_audio_response = test_client_db_reset.post(
        "/audiobook/load_generated_audio",
        params={
            "book_id": 1,
            "chapter_number": 1,
        },
    )
    assert load_audio_response.status_code == HTTP_200_OK
    # Text "Load audio" will be in the response
    load_audio_response_soup = BeautifulSoup(load_audio_response.text, features="lxml")
    assert "Your browser does not support the audio element." in load_audio_response_soup.text
    # Response contains element with <audio> tag
    audio_elements = load_audio_response_soup.find_all("audio")
    assert len(audio_elements) == 1

    # Request to download the audio
    download_mp3_response = test_client_db_reset.get(
        "/audiobook/download_chapter_mp3",
        params={
            "book_id": 1,
            "chapter_number": 1,
        },
    )
    assert download_mp3_response.status_code == HTTP_200_OK
    # Response contains the audio bytes
    assert download_mp3_response.content == example_audio_bytes

    # Request to delete the audio
    delete_audio_response = test_client_db_reset.post(
        "/audiobook/delete_generated_audio",
        params={
            "book_id": 1,
            "chapter_number": 1,
        },
    )
    assert delete_audio_response.status_code == HTTP_200_OK
    delete_audio_response_soup = BeautifulSoup(delete_audio_response.text, features="lxml")
    assert "Generate audio" in delete_audio_response_soup.text

    # Make sure the amount of buttons with "Generate audio" is the same as on after upload
    load_book_afterwards_response = test_client_db_reset.get("/audiobook/book/1")
    assert load_book_afterwards_response.status_code == HTTP_200_OK
    load_book_afterwards_response_soup = BeautifulSoup(load_book_afterwards_response.text, features="lxml")
    chapters_elements_divs = load_book_afterwards_response_soup.find_all("div", id=re.compile(r"chapter_audio_\d+"))
    assert len(chapters_elements_divs) == expected_chapter_count
    generate_audio_buttons_after_delete_audio = load_book_afterwards_response_soup.find_all(
        lambda tag: tag.name == "button" and tag.text.strip() == "Generate audio"
    )
    assert len(generate_audio_buttons_after_delete_audio) == expected_chapter_count


# Test "/generate_audio_book" queues the full book to be converted
# Test "/download_book_zip" downloads a zip file
# Test "/delete_book" deletes the book and all chapters
# Test "/save_settings_to_cookies" sets cookies
