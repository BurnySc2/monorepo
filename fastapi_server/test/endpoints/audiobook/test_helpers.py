"""Unit tests for audiobook route helpers (pure, no DB/S3)."""

from datetime import datetime
from types import SimpleNamespace

import hypothesis.strategies as st
import pytest
from fastapi import HTTPException
from hypothesis import given, settings

from routes._audiobook_helpers import AUDIO_CLEAR_FIELDS, book_to_list_item, parse_chapter_numbers
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


ERR = "chapter_numbers must be comma-separated integers"


@pytest.mark.parametrize(
    ("raw", "want"),
    [
        ("1", [1]),
        ("1,2,3", [1, 2, 3]),
        (" 1, 2 , 3 ", [1, 2, 3]),
        ("  7  ", [7]),
        ("10,20,30", [10, 20, 30]),
        ("0", [0]),
        ("-1,2", [-1, 2]),
    ],
)
def test_parse_valid_table(raw: str, want: list[int]) -> None:
    assert parse_chapter_numbers(raw) == want


@pytest.mark.parametrize(
    ("raw", "detail"),
    [
        (None, "chapter_numbers query param required"),
        ("a,b,c", ERR),
        ("1,foo,3", ERR),
        ("", ERR),
        ("1,2,", ERR),
        ("1,,2", ERR),
        ("   ", ERR),
    ],
)
def test_parse_invalid_table(raw: str | None, detail: str) -> None:
    with pytest.raises(HTTPException) as exc_info:
        parse_chapter_numbers(raw)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == detail


@settings(max_examples=100)
@given(nums=st.lists(st.integers(-10000, 10000), min_size=1, max_size=20))
def test_parse_roundtrip(nums: list[int]) -> None:
    assert parse_chapter_numbers(",".join(str(n) for n in nums)) == nums
    assert parse_chapter_numbers(", ".join(f" {n} " for n in nums)) == nums


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
