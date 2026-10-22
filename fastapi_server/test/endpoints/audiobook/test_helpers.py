"""Unit tests for audiobook route helpers (pure, no DB/S3)."""

from datetime import datetime
from types import SimpleNamespace

from routes._audiobook_helpers import AUDIO_CLEAR_FIELDS, book_to_list_item
from schemas.audiobook.db_models import AudiobookChapter


def _make_book(**overrides):  # type: ignore[no-untyped-def]
    values = {
        "id": 1,
        "uploaded_by": "testuser github",
        "book_title": "Frankenstein; Or, The Modern Prometheus",
        "book_author": "Mary Shelley",
        "custom_book_title": None,
        "custom_book_author": None,
        "chapter_count": 31,
        "upload_date": datetime(2024, 1, 2, 3, 4, 5),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_book_to_list_item_maps_all_fields() -> None:
    book = _make_book()
    item = book_to_list_item(book)  # type: ignore[arg-type]
    assert item.id == 1
    assert item.uploaded_by == "testuser github"
    assert item.book_title == "Frankenstein; Or, The Modern Prometheus"
    assert item.book_author == "Mary Shelley"
    assert item.chapter_count == 31
    assert item.upload_date == datetime(2024, 1, 2, 3, 4, 5)


def test_book_to_list_item_preserves_none_custom_fields() -> None:
    item = book_to_list_item(_make_book())  # type: ignore[arg-type]
    assert item.custom_book_title is None
    assert item.custom_book_author is None


def test_book_to_list_item_preserves_custom_fields() -> None:
    book = _make_book(custom_book_title="My Title", custom_book_author="My Author")
    item = book_to_list_item(book)  # type: ignore[arg-type]
    assert item.custom_book_title == "My Title"
    assert item.custom_book_author == "My Author"


def test_book_to_list_item_preserves_original_title() -> None:
    book = _make_book(custom_book_title="Custom")
    item = book_to_list_item(book)  # type: ignore[arg-type]
    assert item.book_title == "Frankenstein; Or, The Modern Prometheus"
    assert item.custom_book_title == "Custom"


def test_audio_clear_fields_has_four_keys() -> None:
    assert len(AUDIO_CLEAR_FIELDS) == 4


def test_audio_clear_fields_all_values_none() -> None:
    assert all(value is None for value in AUDIO_CLEAR_FIELDS.values())


def test_audio_clear_fields_contains_expected_columns() -> None:
    assert AudiobookChapter.minio_object_name in AUDIO_CLEAR_FIELDS
    assert AudiobookChapter.queued in AUDIO_CLEAR_FIELDS
    assert AudiobookChapter.started_converting in AUDIO_CLEAR_FIELDS
    assert AudiobookChapter.audio_settings in AUDIO_CLEAR_FIELDS
