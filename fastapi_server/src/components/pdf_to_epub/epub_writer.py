"""EPUB writer for the pdf_to_epub feature.

Builds audiobook-compatible EPUBs from T1+T2 Chapter objects so the reader
accepts the output without silent chapter loss. No pymupdf path exists here.
"""

from __future__ import annotations

import gc
import html
import io
import uuid

from ebooklib import epub

from components.pdf_to_epub.chapters import (
    DEFAULT_MAX_CHAPTERS,
    DEFAULT_MIN_CHARS,
    SINGLE_CHUNK_CHARS,
    Chapter,
    NoChaptersError,
)
from components.pdf_to_epub.parser import ExtractedImage

COVER_FILE_NAME = "images/cover.jpg"
NAV_ID = "nav"


def _fallback_title(index: int) -> str:
    return f"Chapter {index}"


def _clean_writer_title(raw: str | None, index: int) -> str:
    cleaned = (raw or "").strip()
    cleaned = " ".join(cleaned.split())
    if not cleaned:
        return _fallback_title(index)
    return cleaned[:200]


def _split_paragraphs(text: str, max_chars: int = 2000) -> list[str]:
    stripped = text.strip()
    if not stripped:
        return []
    words = stripped.split()
    paragraphs: list[str] = []
    current: list[str] = []
    current_len = 0
    for word in words:
        extra = len(word) + (1 if current else 0)
        if current and current_len + extra > max_chars:
            paragraphs.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += extra
    if current:
        paragraphs.append(" ".join(current))
    return paragraphs


def _chapter_body_html(
    title: str,
    text: str,
    image_hrefs: list[str],
    tables_html: list[str],
) -> str:
    # WHY restricted tags: reader feeds get_text straight to TTS, so script/style would be spoken.
    parts: list[str] = [f"<h1>{html.escape(title)}</h1>"]
    for paragraph in _split_paragraphs(text):
        parts.append(f"<p>{html.escape(paragraph)}</p>")
    for table_html in tables_html:
        parts.append(table_html)
    for pos, href in enumerate(image_hrefs, start=1):
        parts.append(f'<img src="{html.escape(href)}" alt="{html.escape(f"Figure {pos}")}"/><br/>')
    return "".join(parts)


def _merge_small_for_writer(chapters: list[Chapter], min_chars: int) -> tuple[list[Chapter], list[str]]:
    warnings: list[str] = []
    if len(chapters) <= 1 or min_chars <= 0:
        return chapters, warnings
    merged: list[Chapter] = []
    for chapter in chapters:
        if not merged:
            merged.append(Chapter(title=chapter.title, text=chapter.text, start_page=chapter.start_page))
            continue
        if len(chapter.text) < min_chars:
            merged[-1].text = f"{merged[-1].text} {chapter.text}".strip()
            warnings.append(f'merged short chapter "{chapter.title}" into previous chapter')
        else:
            merged.append(Chapter(title=chapter.title, text=chapter.text, start_page=chapter.start_page))
    return merged, warnings


def _demote_excess_for_writer(chapters: list[Chapter], max_chapters: int) -> tuple[list[Chapter], list[str]]:
    warnings: list[str] = []
    if max_chapters < 1:
        raise ValueError("max_chapters must be >= 1")
    if len(chapters) <= max_chapters:
        return chapters, warnings
    kept = chapters[:max_chapters]
    excess = chapters[max_chapters:]
    last = kept[-1]
    extras: list[str] = []
    for chapter in excess:
        extras.append(f"{chapter.title} {chapter.text}".strip())
    last.text = f"{last.text} {' '.join(extras)}".strip()
    warnings.append(f"demoted {len(excess)} excess chapters to subheadings in last chapter")
    return kept, warnings


def _split_single_long(chapters: list[Chapter]) -> tuple[list[Chapter], list[str]]:
    warnings: list[str] = []
    if len(chapters) != 1:
        return chapters, warnings
    only = chapters[0]
    if len(only.text) <= SINGLE_CHUNK_CHARS:
        return chapters, warnings
    words = only.text.split()
    chunks: list[Chapter] = []
    current: list[str] = []
    current_len = 0
    for word in words:
        extra = len(word) + (1 if current else 0)
        if current and current_len + extra > SINGLE_CHUNK_CHARS:
            chunk_index = len(chunks) + 1
            suffix = "" if chunk_index == 1 else f" ({chunk_index})"
            chunks.append(Chapter(title=f"{only.title}{suffix}", text=" ".join(current), start_page=only.start_page))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += extra
    if current:
        chunk_index = len(chunks) + 1
        suffix = "" if chunk_index == 1 else f" ({chunk_index})"
        chunks.append(Chapter(title=f"{only.title}{suffix}", text=" ".join(current), start_page=only.start_page))
    warnings.append(f"split long single chapter every {SINGLE_CHUNK_CHARS} characters")
    return chunks, warnings


def _map_images_to_chapters(chapters: list[Chapter], images: list[ExtractedImage]) -> dict[int, list[str]]:
    """Map images to chapters by page_number intervals, each image exactly once."""
    if not chapters or not images:
        return {}
    ordered = sorted(enumerate(chapters), key=lambda pair: pair[1].start_page)
    known_pages = [image.page_number for image in images if image.page_number is not None]
    max_image_page = max(known_pages) if known_pages else None
    max_start = max(chapter.start_page for chapter in chapters)
    last_page = max(max_image_page, max_start) if max_image_page is not None else max_start
    mapped: dict[int, list[str]] = {}
    assigned: set[str] = set()
    for pos, (original_index, chapter) in enumerate(ordered):
        end_page = ordered[pos + 1][1].start_page - 1 if pos + 1 < len(ordered) else last_page
        end_page = max(chapter.start_page, end_page)
        collected: list[str] = []
        for image in images:
            if image.page_number is None or image.file_name in assigned:
                continue
            if chapter.start_page <= image.page_number <= end_page:
                collected.append(image.file_name)
                assigned.add(image.file_name)
        if collected:
            mapped[original_index] = collected
    unassigned = [image.file_name for image in images if image.file_name not in assigned]
    if unassigned:
        first_index = ordered[0][0]
        mapped.setdefault(first_index, []).extend(unassigned)
        for file_name in unassigned:
            assigned.add(file_name)
    return mapped


def build_epub(
    chapters: list[Chapter],
    title: str | None,
    author: str | None,
    language: str = "en",
    identifier: str | None = None,
    images: list[ExtractedImage] | None = None,
    tables_by_chapter: dict[int, list[str]] | None = None,
    use_cover: bool = True,
    min_chars: int = DEFAULT_MIN_CHARS,
    max_chapters: int = DEFAULT_MAX_CHAPTERS,
) -> tuple[epub.EpubBook, list[str]]:
    """Build an audiobook-compatible book with spine, TOC, images, and cover."""
    warnings: list[str] = []
    book_title = (title or "").strip() or "Untitled"
    book_author = (author or "").strip() or "Unknown"
    book_language = (language or "").strip() or "en"
    book_identifier = (identifier or "").strip() or uuid.uuid4().hex
    pending = [Chapter(title=chapter.title, text=chapter.text, start_page=chapter.start_page) for chapter in chapters]
    pending = [chapter for chapter in pending if chapter.text.strip()]
    if not pending:
        raise NoChaptersError("no chapters recoverable: empty document")
    pending, merge_warnings = _merge_small_for_writer(pending, min_chars)
    warnings.extend(merge_warnings)
    pending, demote_warnings = _demote_excess_for_writer(pending, max_chapters)
    warnings.extend(demote_warnings)
    pending, split_warnings = _split_single_long(pending)
    warnings.extend(split_warnings)
    if not pending:
        raise NoChaptersError("no chapters recoverable: empty document")
    cleaned_titles = [_clean_writer_title(chapter.title, pos + 1) for pos, chapter in enumerate(pending)]
    # WHY numbered fallback: untitled or duplicate outline entries still need dual titles.
    seen: set[str] = set()
    for pos, cleaned in enumerate(cleaned_titles):
        lowered = cleaned.lower()
        if lowered in seen:
            cleaned_titles[pos] = _fallback_title(pos + 1)
        else:
            seen.add(lowered)
    image_list = list(images) if images else []
    tables_map = dict(tables_by_chapter) if tables_by_chapter else {}
    image_map = _map_images_to_chapters(pending, image_list)
    book = epub.EpubBook()
    book.set_identifier(book_identifier)
    book.set_title(book_title)
    book.set_language(book_language)
    book.add_author(book_author)
    chapter_items: list[epub.EpubHtml] = []
    for pos, (chapter, cleaned_title) in enumerate(zip(pending, cleaned_titles, strict=True)):
        file_name = f"chap_{pos + 1:04d}.xhtml"
        chapter_tables = list(tables_map.get(pos, []))
        # WHY page-mapped: images follow chapter page intervals like tables, each exactly once.
        per_chapter = list(image_map.get(pos, []))
        body_inner = _chapter_body_html(cleaned_title, chapter.text, per_chapter, chapter_tables)
        content = f"<html><head><title>{html.escape(cleaned_title)}</title></head><body>{body_inner}</body></html>"
        item = epub.EpubHtml(
            uid=f"chap_{pos + 1:04d}",
            file_name=file_name,
            title=cleaned_title,
            content=content,
            lang=book_language,
        )
        book.add_item(item)
        chapter_items.append(item)
    for image in image_list:
        book.add_item(
            epub.EpubImage(uid=None, file_name=image.file_name, media_type=image.media_type, content=image.data)
        )
    if use_cover and image_list:
        cover_data = image_list[0].data
        book.set_cover(COVER_FILE_NAME, cover_data, create_page=False)
        for idx, item in enumerate(book.items):
            if type(item) is epub.EpubCover and item.file_name == COVER_FILE_NAME:
                replacement = epub.EpubImage(
                    uid="cover-img", file_name=COVER_FILE_NAME, media_type="image/jpeg", content=cover_data
                )
                replacement.id = item.id
                replacement.book = book
                book.items[idx] = replacement
                break
    # pyrefly: ignore[bad-assignment]
    book.toc = tuple(
        epub.Link(item.file_name, cleaned_title, f"toc_{pos + 1:04d}")
        for pos, (item, cleaned_title) in enumerate(zip(chapter_items, cleaned_titles, strict=True))
    )
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = [NAV_ID, *chapter_items]
    gc.collect()
    return book, warnings


def write_epub_bytes(
    chapters: list[Chapter],
    title: str | None,
    author: str | None,
    language: str = "en",
    identifier: str | None = None,
    images: list[ExtractedImage] | None = None,
    tables_by_chapter: dict[int, list[str]] | None = None,
    use_cover: bool = True,
    min_chars: int = DEFAULT_MIN_CHARS,
    max_chapters: int = DEFAULT_MAX_CHAPTERS,
) -> tuple[bytes, list[str]]:
    """Write chapters to EPUB bytes with compat guarantees."""
    book, warnings = build_epub(
        chapters,
        title,
        author,
        language,
        identifier,
        images,
        tables_by_chapter,
        use_cover,
        min_chars,
        max_chapters,
    )
    buffer = io.BytesIO()
    epub.write_epub(buffer, book, {})
    gc.collect()
    return buffer.getvalue(), warnings


def roundtrip_validate(
    epub_bytes: bytes,
    expected_title: str,
    expected_author: str,
    expected_titles: list[str],
) -> None:
    """Read back via audiobook reader and assert title, author, count, and titles."""
    from components.audiobook.epub_reader import extract_chapters, extract_metadata

    metadata = extract_metadata(io.BytesIO(epub_bytes))
    assert metadata.title == expected_title, f"title mismatch: {metadata.title!r} != {expected_title!r}"
    assert metadata.author == expected_author, f"author mismatch: {metadata.author!r} != {expected_author!r}"
    read_chapters = extract_chapters(io.BytesIO(epub_bytes))
    # WHY nav filter: single-chapter fallback counts EpubNav as a chapter via items fallback.
    content_chapters = [chapter for chapter in read_chapters if chapter.chapter_title != NAV_ID]
    assert len(content_chapters) == len(expected_titles), (
        f"chapter count mismatch: {len(content_chapters)} != {len(expected_titles)}"
    )
    for read_chapter, expected in zip(content_chapters, expected_titles, strict=True):
        assert read_chapter.chapter_title == expected, (
            f"chapter title mismatch: {read_chapter.chapter_title!r} != {expected!r}"
        )
    gc.collect()
