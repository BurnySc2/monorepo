import io
import os
import re
from pathlib import Path
from unittest.mock import AsyncMock, patch
from zipfile import ZipFile

import pytest
from bs4 import BeautifulSoup  # pyre-fixme[21]
from litestar.contrib.htmx._utils import HTMXHeaders
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED
from litestar.testing import TestClient
from minio import Minio, S3Error
from pytest_httpx import HTTPXMock

from prisma import Prisma
from src.routes.caches import global_cache
from src.workers import convert_audiobook
from src.workers.convert_audiobook import convert_one
from test.base_test import log_in_with_twitch, test_client, test_client_db_reset, test_minio_client  # noqa: F401

_test_client = test_client
_test_client_db_reset = test_client_db_reset
_test_minio_client = test_minio_client


def test_index_route_inaccessable_when_not_logged_in(test_client: TestClient) -> None:  # noqa: F811
    response = test_client.get("/audiobook/epub_upload")
    assert response.status_code == HTTP_401_UNAUTHORIZED


# Test "/audiobook/epub_upload" has upload button
@pytest.mark.asyncio
async def test_index_route_has_upload_button(test_client_db_reset: TestClient, httpx_mock: HTTPXMock) -> None:  # noqa: F811
    await global_cache.delete_all()
    log_in_with_twitch(test_client_db_reset, httpx_mock)
    response = test_client_db_reset.get("/audiobook/epub_upload")
    assert response.status_code == HTTP_200_OK
    # assert button exists with text "Upload"
    soup = BeautifulSoup(response.text, features="lxml")
    assert len(soup.find_all("button", type="submit")) == 1


# Test post request to "/audiobook/epub_upload" can upload an epub
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
    await global_cache.delete_all()
    log_in_with_twitch(test_client_db_reset, httpx_mock)

    # Sanity check
    async with Prisma() as db:
        count = await db.audiobookbook.count()
        assert count == 0
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
    await global_cache.delete_all()
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


# Test "/delete_book" can remove book
@pytest.mark.httpx_mock(non_mocked_hosts=["localhost"])
@pytest.mark.asyncio
async def test_delete_book_works(test_client_db_reset: TestClient, httpx_mock: HTTPXMock) -> None:  # noqa: F811
    await global_cache.delete_all()
    log_in_with_twitch(test_client_db_reset, httpx_mock)

    book_before_upload_response = test_client_db_reset.get("/audiobook/book/1")
    assert book_before_upload_response.status_code == HTTP_401_UNAUTHORIZED

    # Pre condition: no book uploaded
    async with Prisma() as db:
        uploaded_books_pre_upload = await db.audiobookbook.count(where={})
        assert uploaded_books_pre_upload == 0
        uploaded_chapters_pre_upload = await db.audiobookchapter.count(where={})
        assert uploaded_chapters_pre_upload == 0

    # Upload book
    expected_chapter_count = 31
    book_path = Path(__file__).parent / "actual_books/frankenstein.epub"
    upload_book_response = test_client_db_reset.post(
        "/audiobook/epub_upload", files={"upload-file": book_path.open("rb")}
    )
    assert upload_book_response.status_code == HTTP_201_CREATED
    # TODO Check redirect content

    # Condition: book was successfully entered
    async with Prisma() as db:
        uploaded_books_post_upload = await db.audiobookbook.count(where={})
        assert uploaded_books_post_upload == 1
        uploaded_chapters_post_upload = await db.audiobookchapter.count(where={})
        assert uploaded_chapters_post_upload == expected_chapter_count

    book_after_upload_response = test_client_db_reset.get("/audiobook/book/1")
    assert book_after_upload_response.status_code == HTTP_200_OK

    # Delete book
    delete_book_response = test_client_db_reset.post(
        "/audiobook/delete_book",
        params={"book_id": 1},
    )
    assert delete_book_response.status_code == HTTP_201_CREATED

    # Post condition: book has been deleted, no book in db
    async with Prisma() as db:
        uploaded_books_post_upload = await db.audiobookbook.count(where={})
        assert uploaded_books_post_upload == 0
        uploaded_chapters_post_upload = await db.audiobookchapter.count(where={})
        assert uploaded_chapters_post_upload == 0

    # Book has been deleted
    book_after_delete_response = test_client_db_reset.get("/audiobook/book/1")
    assert book_after_delete_response.status_code == HTTP_401_UNAUTHORIZED


# Test "/generate_audio" can generate audio for a chapter
@pytest.mark.httpx_mock(non_mocked_hosts=["localhost"])
@pytest.mark.asyncio
async def test_generate_audio_for_chapter(
    test_client_db_reset: TestClient, test_minio_client: Minio, httpx_mock: HTTPXMock
) -> None:  # noqa: F811
    await global_cache.delete_all()
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

    # Make sure generated audio was saved in minio
    assert test_minio_client.bucket_exists(os.getenv("MINIO_AUDIOBOOK_BUCKET"))
    assert test_minio_client.stat_object(os.getenv("MINIO_AUDIOBOOK_BUCKET"), "1_audio.mp3")

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
    # Make sure the audio was deleted in minio too
    with pytest.raises(S3Error):
        # Raises error if object does not exist
        test_minio_client.stat_object(os.getenv("MINIO_AUDIOBOOK_BUCKET"), "1_audio.mp3")

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


# TODO Mark test as slow?
# Test "/generate_audio_book" requests audio for all chapters
# and "/download_book_zip" generates zip file with audio files of all chapters
@pytest.mark.httpx_mock(non_mocked_hosts=["localhost"])
@pytest.mark.asyncio
async def test_generate_audio_for_entire_book(
    test_client_db_reset: TestClient, test_minio_client: Minio, httpx_mock: HTTPXMock
) -> None:  # noqa: F811
    await global_cache.delete_all()
    log_in_with_twitch(test_client_db_reset, httpx_mock)

    # Upload book
    expected_chapter_count = 31
    book_path = Path(__file__).parent / "actual_books/frankenstein.epub"
    upload_book_response = test_client_db_reset.post(
        "/audiobook/epub_upload", files={"upload-file": book_path.open("rb")}
    )
    assert upload_book_response.status_code == HTTP_201_CREATED

    request_generate_audio_for_book_response = test_client_db_reset.post(
        "/audiobook/generate_audio_book", params={"book_id": 1}
    )
    assert request_generate_audio_for_book_response.status_code == HTTP_201_CREATED

    # Generate audio for each chapter
    for i in range(expected_chapter_count):
        with patch.object(
            convert_audiobook,
            "generate_text_to_speech",
            new=AsyncMock(
                return_value=io.BytesIO(f"bytes for audio {i+1}".encode()),
            ),
        ):
            await convert_one()

        # Make sure it was saved in database and in minio
        async with Prisma() as db:
            audio_chapter_generated = await db.audiobookchapter.count(where={"minio_object_name": f"{i+1}_audio.mp3"})
            assert audio_chapter_generated == 1
        assert test_minio_client.bucket_exists(os.getenv("MINIO_AUDIOBOOK_BUCKET"))
        assert test_minio_client.stat_object(os.getenv("MINIO_AUDIOBOOK_BUCKET"), f"{i+1}_audio.mp3")

    # Test download-zip works (only if audio for all chapters are generated)
    download_zip_response = test_client_db_reset.get("/audiobook/download_book_zip", params={"book_id": 1})
    assert download_zip_response.status_code == HTTP_200_OK
    zip_file = ZipFile(io.BytesIO(download_zip_response.content))
    assert len(zip_file.filelist) == expected_chapter_count
    for index, mp3_file in enumerate(zip_file.filelist, start=1):
        assert mp3_file.filename.startswith(
            f"Mary Wollstonecraft Shelley/Frankenstein Or The Modern Prometheus/{index:04d}_"
        )
        assert mp3_file.filename.endswith(".mp3")

    delete_book_response = test_client_db_reset.post("/audiobook/delete_book", params={"book_id": 1})
    assert delete_book_response.status_code == HTTP_201_CREATED
    # Test deletion of book deletes database entries
    async with Prisma() as db:
        uploaded_books_post_delete = await db.audiobookbook.count(where={})
        assert uploaded_books_post_delete == 0
        uploaded_chapters_post_delete = await db.audiobookchapter.count(where={})
        assert uploaded_chapters_post_delete == 0

    # Test deletion of book deletes minio entries
    for i in range(expected_chapter_count):
        with pytest.raises(S3Error):
            # Raises error if object does not exist
            test_minio_client.stat_object(os.getenv("MINIO_AUDIOBOOK_BUCKET"), f"{i+1}_audio.mp3")


# Test "/save_settings_to_cookies" sets cookies
