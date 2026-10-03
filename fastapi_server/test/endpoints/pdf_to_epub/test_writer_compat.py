"""Writer compat tests for the pdf_to_epub feature.

Covers SPEC section 13 writer MUSTs: metadata, file identity, spine order,
dual titles, restricted body, image cover, empties handling, and read-back.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from ebooklib import epub
from PIL import Image

from components.audiobook.epub_reader import extract_chapters, extract_metadata
from components.pdf_to_epub.chapters import Chapter, NoChaptersError
from components.pdf_to_epub.epub_writer import build_epub, roundtrip_validate, write_epub_bytes
from components.pdf_to_epub.parser import (
    MAX_IMAGE_BYTES,
    MAX_IMAGE_WIDTH,
    ExtractedImage,
    PageText,
    detect_mojibake_warnings,
    extract_images,
    extract_tables_html,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _long_text(prefix: str, repeats: int = 200) -> str:
    return f"{prefix} " + " ".join(["body"] * repeats)


def _sample_chapters() -> list[Chapter]:
    return [
        Chapter(title="Intro", text=_long_text("First chapter."), start_page=1),
        Chapter(title="Middle", text=_long_text("Second chapter."), start_page=2),
        Chapter(title="Finale", text=_long_text("Third chapter."), start_page=3),
    ]


def _make_test_image(file_name: str, width: int = 10, height: int = 10) -> ExtractedImage:
    picture = Image.new("RGB", (width, height), color=(200, 30, 30))
    buffer = io.BytesIO()
    picture.save(buffer, format="JPEG", quality=70)
    return ExtractedImage(
        file_name=file_name,
        data=buffer.getvalue(),
        media_type="image/jpeg",
        width=width,
        height=height,
        page_number=1,
    )


def test_write_roundtrip_metadata_and_chapters() -> None:
    chapters = _sample_chapters()
    data, _warnings = write_epub_bytes(chapters, "Compat Title", "Compat Author", "en", "compat-id-1")
    metadata = extract_metadata(io.BytesIO(data))
    assert metadata.title == "Compat Title"
    assert metadata.author == "Compat Author"
    read_chapters = extract_chapters(io.BytesIO(data))
    content_chapters = [chapter for chapter in read_chapters if chapter.chapter_title != "nav"]
    assert len(content_chapters) == 3
    assert [chapter.chapter_title for chapter in content_chapters] == ["Intro", "Middle", "Finale"]
    roundtrip_validate(data, "Compat Title", "Compat Author", ["Intro", "Middle", "Finale"])


def test_spine_order_matches_toc_and_chapters() -> None:
    chapters = _sample_chapters()
    book, _warnings = build_epub(chapters, "Spine Title", "Spine Author")
    assert book.spine[0] == "nav"
    spine_items = book.spine[1:]
    assert len(spine_items) == 3
    assert [item.file_name for item in spine_items] == ["chap_0001.xhtml", "chap_0002.xhtml", "chap_0003.xhtml"]
    toc_hrefs = [link.href for link in book.toc]  # type: ignore[attr-defined]
    assert toc_hrefs == ["chap_0001.xhtml", "chap_0002.xhtml", "chap_0003.xhtml"]


def test_href_equals_file_name_no_fragments_and_dual_titles() -> None:
    chapters = _sample_chapters()
    book, _warnings = build_epub(chapters, "Href Title", "Href Author")
    chapter_by_href = {item.file_name: item for item in book.spine[1:]}
    for link in book.toc:  # type: ignore[attr-defined]
        assert "#" not in link.href
        assert link.href == chapter_by_href[link.href].file_name
        assert link.title == chapter_by_href[link.href].title
    for item in book.spine[1:]:
        assert item.file_name.startswith("chap_") and item.file_name.endswith(".xhtml")


def test_duplicate_titles_get_chapter_n_fallback() -> None:
    chapters = [
        Chapter(title="Intro", text=_long_text("Alpha."), start_page=1),
        Chapter(title="Intro", text=_long_text("Beta."), start_page=2),
        Chapter(title="", text=_long_text("Gamma."), start_page=3),
    ]
    data, _warnings = write_epub_bytes(chapters, "Dup Title", "Dup Author", "dup-id")
    roundtrip_validate(data, "Dup Title", "Dup Author", ["Intro", "Chapter 2", "Chapter 3"])


def test_body_has_no_script_or_style() -> None:
    tables_by_chapter = {0: ["<table><tr><td>a</td><td>b</td></tr></table>"]}
    images = [_make_test_image("images/img_0001.jpg")]
    book, _warnings = build_epub(
        _sample_chapters(), "Body Title", "Body Author", images=images, tables_by_chapter=tables_by_chapter
    )
    for item in book.items:
        if isinstance(item, epub.EpubHtml) and item.file_name.startswith("chap_"):
            content = item.content if isinstance(item.content, str) else item.content.decode("utf-8")
            lowered = content.lower()
            assert "<script" not in lowered
            assert "<style" not in lowered
            assert "<p>" in lowered or "<h1>" in lowered
    first_content = book.spine[1].content
    first_text = first_content if isinstance(first_content, str) else first_content.decode("utf-8")
    assert "<table>" in first_text.lower()
    assert "<img" in first_text.lower()


def test_cover_is_epub_image_not_html() -> None:
    images = [_make_test_image("images/img_0001.jpg"), _make_test_image("images/img_0002.jpg")]
    book, _warnings = build_epub(_sample_chapters(), "Cover Title", "Cover Author", images=images, use_cover=True)
    cover_items = [item for item in book.items if item.file_name == "images/cover.jpg"]
    assert len(cover_items) == 1
    assert isinstance(cover_items[0], epub.EpubImage)
    html_covers = [item for item in book.items if isinstance(item, epub.EpubHtml) and "cover" in item.file_name.lower()]
    assert html_covers == []
    inline_images = [item for item in book.items if isinstance(item, epub.EpubImage)]
    assert len(inline_images) >= 3


def test_cover_disabled_has_no_cover_file() -> None:
    images = [_make_test_image("images/img_0001.jpg")]
    book, _warnings = build_epub(_sample_chapters(), "No Cover", "No Author", images=images, use_cover=False)
    assert [item for item in book.items if item.file_name == "images/cover.jpg"] == []


def test_empties_merge_and_zero_guard() -> None:
    chapters = [
        Chapter(title="Intro", text=_long_text("Alpha."), start_page=1),
        Chapter(title="Stub", text="tiny", start_page=2),
        Chapter(title="Finale", text=_long_text("Beta."), start_page=3),
    ]
    book, _warnings = build_epub(chapters, "Merge Title", "Merge Author", min_chars=500)
    assert len(book.spine[1:]) == 2
    with pytest.raises(NoChaptersError):
        write_epub_bytes([], "Empty", "Nobody")
    with pytest.raises(NoChaptersError):
        write_epub_bytes([Chapter(title="Blank", text="   ", start_page=1)], "Empty", "Nobody")


def test_images_extract_dedupe_and_caps() -> None:
    data = (FIXTURES / "outline.pdf").read_bytes()
    images, warnings = extract_images(data)
    assert warnings == [] or all(isinstance(warning, str) for warning in warnings)
    assert len(images) == 1
    seen_hashes = set()
    for image in images:
        assert image.file_name.startswith("images/img_") and image.file_name.endswith(".jpg")
        assert image.media_type == "image/jpeg"
        assert image.width <= MAX_IMAGE_WIDTH
        assert len(image.data) <= MAX_IMAGE_BYTES
        assert image.data[:2] == b"\xff\xd8"
        seen_hashes.add(image.file_name)
    assert len(seen_hashes) == len(images)
    empty_images, _empty_warnings = extract_images((FIXTURES / "small_text.pdf").read_bytes())
    assert empty_images == []


def test_tables_minimal_warns_and_balanced_html() -> None:
    data = (FIXTURES / "small_text.pdf").read_bytes()
    balanced_tables, balanced_warnings = extract_tables_html(data, 1, parser="balanced", include_tables=True)
    assert balanced_warnings == []
    assert balanced_tables == []
    minimal_tables, minimal_warnings = extract_tables_html(data, 1, parser="minimal", include_tables=True)
    assert minimal_tables == []
    assert any("minimal" in warning.lower() for warning in minimal_warnings)


def test_mojibake_warnings_do_not_fail() -> None:
    pages = [PageText(page_number=1, text="clean intro text"), PageText(page_number=2, text="broken � text")]
    warnings = detect_mojibake_warnings(pages)
    assert len(warnings) == 1
    assert "page 2" in warnings[0].lower()
    assert detect_mojibake_warnings([PageText(page_number=1, text="clean")]) == []
