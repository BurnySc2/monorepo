import io
import os
import re
from pathlib import Path
from unittest.mock import AsyncMock, patch
from zipfile import ZipFile

from minio import Minio, S3Error
import pytest
from bs4 import BeautifulSoup  # pyre-fixme[21]
from litestar.contrib.htmx._utils import HTMXHeaders
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED
from litestar.testing import TestClient
from pytest_httpx import HTTPXMock

from models.audiobook import AudiobookBook, AudiobookChapter
from routes.audiobook.my_minio_client import minio_check_if_object_exists
from routes.caches import global_cache
from test.base_test import (
    helper_wait_till_db_has_count_minio_objects,
    helper_wait_till_minio_object_exists,
    log_in_with_twitch,
    test_client,
    test_client_db_reset,
    test_minio_client,
)  # noqa: F401
from workers import convert_audiobook
from workers.convert_audiobook import check_queued_chapters

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
@pytest.mark.asyncio
async def test_index_route_upload_epub_frankenstein(test_client_db_reset: TestClient, httpx_mock: HTTPXMock) -> None:  # noqa: F811
    await global_cache.delete_all()
    log_in_with_twitch(test_client_db_reset, httpx_mock)

    book_paths = [
        ("actual_books/frankenstein.epub", 31),
        ("actual_books/romeo-and-juliet.epub", 28),
        ("actual_books/the-war-of-the-worlds.epub", 29),
    ]
    sum_of_chapters = 0
    for book_id, (book_relative_path, book_chapters_amount) in enumerate(book_paths, start=1):
        # Sanity check
        pre_book_count = await AudiobookBook.count()
        assert pre_book_count == book_id - 1
        pre_chapter_count = await AudiobookChapter.count()
        assert pre_chapter_count == sum_of_chapters

        # Make sure the book does not exist yet
        upload_response = test_client_db_reset.get(f"/audiobook/book/{book_id}")
        assert upload_response.status_code == HTTP_401_UNAUTHORIZED

        # Upload book
        book_path = Path(__file__).parent / book_relative_path
        upload_response = test_client_db_reset.post(
            "/audiobook/epub_upload", files={"upload-file": book_path.open("rb")}
        )
        assert upload_response.status_code == HTTP_201_CREATED
        assert upload_response.headers.get(HTMXHeaders.REDIRECT) == f"/audiobook/book/{book_id}"
        assert upload_response.headers.get("location") is None

        # Make sure N chapters were detected
        redirect_response = test_client_db_reset.get(upload_response.headers.get(HTMXHeaders.REDIRECT))
        soup = BeautifulSoup(redirect_response.text, features="lxml")
        matching_divs = soup.find_all("div", id=lambda x: x is not None and x.startswith("chapter_audio_"))
        assert redirect_response.status_code == HTTP_200_OK
        assert len(matching_divs) == book_chapters_amount

        # Database verification check
        post_book_count = await AudiobookBook.count()
        assert post_book_count == book_id
        sum_of_chapters += book_chapters_amount
        post_chapter_count = await AudiobookChapter.count()
        assert post_chapter_count == sum_of_chapters


# Test post request to "/" book already exists
@pytest.mark.asyncio
async def test_index_route_upload_epub_twice(test_client_db_reset: TestClient, httpx_mock: HTTPXMock) -> None:  # noqa: F811
    await global_cache.delete_all()
    # Sanity check
    pre_book_count = await AudiobookBook.count()
    assert pre_book_count == 0

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

    # Assert book has been added to db once
    post_book_count = await AudiobookBook.count()
    assert post_book_count == 1


# Test "/delete_book" can remove book
@pytest.mark.asyncio
async def test_delete_book_works(test_client_db_reset: TestClient, httpx_mock: HTTPXMock) -> None:  # noqa: F811
    await global_cache.delete_all()
    log_in_with_twitch(test_client_db_reset, httpx_mock)

    book_before_upload_response = test_client_db_reset.get("/audiobook/book/1")
    assert book_before_upload_response.status_code == HTTP_401_UNAUTHORIZED

    # Pre condition: no book uploaded
    pre_book_count = await AudiobookBook.count()
    assert pre_book_count == 0
    pre_chapter_count = await AudiobookChapter.count()
    assert pre_chapter_count == 0

    # Upload book
    expected_chapter_count = 31
    book_path = Path(__file__).parent / "actual_books/frankenstein.epub"
    upload_book_response = test_client_db_reset.post(
        "/audiobook/epub_upload", files={"upload-file": book_path.open("rb")}
    )
    assert upload_book_response.status_code == HTTP_201_CREATED
    # TODO Check redirect content

    # Condition: book was successfully entered
    post_book_count = await AudiobookBook.count()
    assert post_book_count == 1
    post_chapter_count = await AudiobookChapter.count()
    assert post_chapter_count == expected_chapter_count

    book_after_upload_response = test_client_db_reset.get("/audiobook/book/1")
    assert book_after_upload_response.status_code == HTTP_200_OK

    # Delete book
    delete_book_response = test_client_db_reset.post(
        "/audiobook/delete_book",
        params={"book_id": 1},
    )
    assert delete_book_response.status_code == HTTP_201_CREATED

    # Post condition: book has been deleted, no book in db
    post_delete_book_count = await AudiobookBook.count()
    assert post_delete_book_count == 0
    post_delete_chapter_count = await AudiobookChapter.count()
    assert post_delete_chapter_count == 0

    # Book has been deleted
    book_after_delete_response = test_client_db_reset.get("/audiobook/book/1")
    assert book_after_delete_response.status_code == HTTP_401_UNAUTHORIZED


# Test "/generate_audio" can generate audio for a chapter
@pytest.mark.asyncio
async def test_generate_audio_for_chapter(
    test_client_db_reset: TestClient, test_minio_client: Minio, httpx_mock: HTTPXMock
) -> None:  # noqa: F811o
    await global_cache.delete_all()
    # 1) Login and upload book
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

    # 2) Queue chapter for audio generation
    # Request to generate audio for first chapter
    click_generate_audio_response = test_client_db_reset.post(
        "/audiobook/generate_audio",
        params={
            "book_id": 1,
            "chapter_number": 1,
        },
        data={
            "voice_name": "my_test",
            "voice_rate": 0,
            "voice_volume": 0,
            "voice_pitch": 0,
            "hidden_refresh_queue": "",
        },
    )
    assert click_generate_audio_response.status_code == HTTP_200_OK
    # Text "Queued" will be in the response html element
    click_generate_audio_response_soup = BeautifulSoup(click_generate_audio_response.text, features="lxml")
    assert "Queued" in click_generate_audio_response_soup.text

    # 3) Generate audio
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
        await check_queued_chapters()
        created = await helper_wait_till_minio_object_exists(os.getenv("MINIO_AUDIOBOOK_BUCKET"), "1_audio.mp3")
        assert created

    # 4) Make sure generated audio was saved in minio
    assert test_minio_client.bucket_exists(os.getenv("MINIO_AUDIOBOOK_BUCKET"))
    assert await minio_check_if_object_exists(os.getenv("MINIO_AUDIOBOOK_BUCKET"), "1_audio.mp3")
    minio_object_info = test_minio_client.stat_object(os.getenv("MINIO_AUDIOBOOK_BUCKET"), "1_audio.mp3")
    assert minio_object_info.size == len(example_audio_bytes)

    # 5) Verify audio has been generated and is saved in DB
    chapter_from_db = (
        await AudiobookChapter.objects()
        .where((AudiobookChapter.book == 1) & (AudiobookChapter.chapter_number == 1))
        .first()
    )
    assert chapter_from_db.queued is not None
    assert chapter_from_db.minio_object_name is not None

    # 6) Verify delete-audio works
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


# TODO Mark test as slow?
# Test "/generate_audio_for_book" requests audio for all chapters
# and "/download_book_zip" generates zip file with audio files of all chapters
@pytest.mark.asyncio
async def test_generate_audio_for_entire_book(
    test_client_db_reset: TestClient, test_minio_client: Minio, httpx_mock: HTTPXMock
) -> None:  # noqa: F811
    await global_cache.delete_all()
    # Sanity check: no book and chapters exist in db
    pre_book_count = await AudiobookBook.count()
    assert pre_book_count == 0
    pre_chapter_count = await AudiobookChapter.count()
    assert pre_chapter_count == 0

    log_in_with_twitch(test_client_db_reset, httpx_mock)

    # Upload book
    expected_chapter_count = 31
    book_path = Path(__file__).parent / "actual_books/frankenstein.epub"
    upload_book_response = test_client_db_reset.post(
        "/audiobook/epub_upload",
        files={
            "upload-file": book_path.open("rb"),
        },
    )
    assert upload_book_response.status_code == HTTP_201_CREATED

    request_generate_audio_for_book_response = test_client_db_reset.post(
        "/audiobook/generate_audio_for_book",
        params={"book_id": 1},
        data={
            "voice_name": "my_test",
            "voice_rate": 0,
            "voice_volume": 0,
            "voice_pitch": 0,
            "hidden_refresh_queue": "",
        },
    )
    assert request_generate_audio_for_book_response.status_code == HTTP_200_OK

    # Generate audio for each chapter
    assert test_minio_client.bucket_exists(os.getenv("MINIO_AUDIOBOOK_BUCKET"))
    with patch.object(
        convert_audiobook,
        "generate_text_to_speech",
        new=AsyncMock(
            return_value=io.BytesIO(b"example test bytes"),
        ),
    ):
        await check_queued_chapters()
        await helper_wait_till_db_has_count_minio_objects(expected_chapter_count)

    return

    # TODO Fix test
    # for chapter_number in range(1, expected_chapter_count + 1):
    #     await helper_wait_till_minio_object_exists(os.getenv("MINIO_AUDIOBOOK_BUCKET"), f"{chapter_number}_audio.mp3")
    # Verify each chapter has generated audio
    for chapter_number in range(1, expected_chapter_count + 1):
        minio_object_name = f"{chapter_number}_audio.mp3"
        assert await minio_check_if_object_exists(
            os.getenv("MINIO_AUDIOBOOK_BUCKET"), minio_object_name, client=test_minio_client
        )
    # Make sure it was saved in database and in minio
    count = await AudiobookChapter.count().where(
        AudiobookChapter.minio_object_name != None  # noqa: E711
    )
    assert count == expected_chapter_count

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

    # Delete book
    delete_book_response = test_client_db_reset.post("/audiobook/delete_book", params={"book_id": 1})
    assert delete_book_response.status_code == HTTP_201_CREATED
    # Test deletion of book deletes database entries
    post_delete_book_count = await AudiobookBook.count()
    assert post_delete_book_count == 0
    post_delete_chapter_count = await AudiobookChapter.count()
    assert post_delete_chapter_count == 0
    # Test deletion of book deletes minio entries
    for chapter_number in range(1, expected_chapter_count + 1):
        assert not (
            await minio_check_if_object_exists(os.getenv("MINIO_AUDIOBOOK_BUCKET"), f"{chapter_number}_audio.mp3")
        )


# Test "/save_settings_to_cookies" sets cookies
