from __future__ import annotations

import gc
import io
import json
import logging
from typing import Annotated, Literal
from urllib.parse import quote

from ebooklib import epub
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from components.pdf_to_epub.chapters import (
    SINGLE_FALLBACK_WARNING,
    Chapter,
    NoChaptersError,
    cleanup_text,
    detect_chapters,
)
from components.pdf_to_epub.epub_writer import build_epub, roundtrip_validate
from components.pdf_to_epub.parser import (
    EncryptedPdfError,
    MaxQualityDisabledError,
    OutlineEntry,
    PageText,
    ScannedPdfError,
    detect_mojibake_warnings,
    extract_all_tables_html,
    extract_images,
    extract_outline,
    extract_pages,
    probe_pdf,
)

pdf_to_epub_router = APIRouter()

logger = logging.getLogger(__name__)

MAX_PDF_SIZE_BYTES = 100 * 1024 * 1024
PREVIEW_CHARS = 500
MAX_QUALITY_DISABLED_DETAIL = "max_quality parser is disabled; use balanced or minimal"
MAX_TITLE_CHARS = 200
MAX_AUTHOR_CHARS = 200
MAX_LANGUAGE_CHARS = 20
GENERIC_400_DETAIL = "invalid or unreadable PDF"

ParserChoice = Literal["balanced", "minimal", "max_quality"]
ChapterModeChoice = Literal["auto", "outline", "heuristic", "single"]
SensitivityChoice = Literal["low", "medium", "high"]
ChapterSourceChoice = Literal["outline", "heuristic", "single"]


class PdfProbeMetadata(BaseModel):
    title: str | None
    author: str | None
    language: str | None


class PdfProbeResult(BaseModel):
    total_pages: int
    has_outline: bool
    has_images: bool
    metadata: PdfProbeMetadata


class PdfPreviewChapter(BaseModel):
    title: str
    chars: int
    preview: str


class PdfPreviewResult(BaseModel):
    chapter_source: ChapterSourceChoice
    outline: list[str]
    chapters: list[PdfPreviewChapter]
    warnings: list[str]


def _ensure_pdf_magic(data: bytes) -> None:
    if not data[:1024].lstrip().startswith(b"%PDF"):
        raise HTTPException(status_code=415, detail="not a PDF file")


def _ensure_pdf_size(data: bytes) -> None:
    if len(data) > MAX_PDF_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="file too large")


def _ensure_parser_enabled(parser: str) -> None:
    if parser == "max_quality":
        raise HTTPException(status_code=422, detail=MAX_QUALITY_DISABLED_DETAIL)


def _sanitize_filename(title: str) -> str:
    base = (title or "").strip() or "Untitled"
    safe = "".join(char if char.isalnum() or char in (" ", "-", "_", ".") else "_" for char in base).strip()
    safe = " ".join(safe.split())
    if not safe:
        safe = "Untitled"
    if len(safe) > 100:
        safe = safe[:100].strip() or "Untitled"
    return f"{safe}.epub"


def _cap_text(value: str, limit: int) -> str:
    capped = (value or "").strip()
    if len(capped) > limit:
        capped = capped[:limit].strip()
    return capped


def _to_preview_chapter(chapter: Chapter, clean_hyphens: bool) -> PdfPreviewChapter:
    # WHY re-clean: detection normalizes text; flag keeps API compat for hyphen handling.
    text = cleanup_text(chapter.text, clean_hyphens=clean_hyphens)
    return PdfPreviewChapter(title=chapter.title, chars=len(text), preview=text[:PREVIEW_CHARS])


def _map_tables_to_chapters(chapters: list[Chapter], tables_by_page: dict[int, list[str]]) -> dict[int, list[str]]:
    if not chapters or not tables_by_page:
        return {}
    ordered = sorted(enumerate(chapters), key=lambda pair: pair[1].start_page)
    max_table_page = max(tables_by_page.keys())
    max_start = max(chapter.start_page for chapter in chapters)
    last_page = max(max_table_page, max_start)
    mapped: dict[int, list[str]] = {}
    for pos, (original_index, chapter) in enumerate(ordered):
        end_page = ordered[pos + 1][1].start_page - 1 if pos + 1 < len(ordered) else last_page
        end_page = max(chapter.start_page, end_page)
        collected: list[str] = []
        for page_number in range(chapter.start_page, end_page + 1):
            collected.extend(tables_by_page.get(page_number, []))
        if collected:
            mapped[original_index] = collected
    return mapped


def _apply_chapter_title_overrides(chapters: list[Chapter], raw: str | None) -> None:
    # WHY in-place override: detected order drives tables mapping and writer TOC.
    if raw is None:
        return
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail="invalid chapter_titles JSON") from exc
    if not isinstance(parsed, list):
        raise HTTPException(status_code=400, detail="chapter_titles must be a JSON list of strings")
    if len(parsed) != len(chapters):
        raise HTTPException(
            status_code=400,
            detail=f"chapter_titles length {len(parsed)} does not match detected chapters {len(chapters)}",
        )
    for entry in parsed:
        if not isinstance(entry, str):
            raise HTTPException(status_code=400, detail="chapter_titles entries must be strings")
    for index, entry in enumerate(parsed):
        cleaned = entry.strip()
        if not cleaned:
            continue
        chapters[index].title = cleaned[:200]


def _resolve_book_metadata(
    title: str | None, author: str | None, language: str | None, data: bytes
) -> tuple[str, str, str]:
    probed_title: str | None = None
    probed_author: str | None = None
    probed_language: str | None = None
    try:
        probed = probe_pdf(data)
        probed_title = probed.metadata.title
        probed_author = probed.metadata.author
        probed_language = probed.metadata.language
    except Exception:  # noqa: BLE001
        logger.debug("probe for book metadata failed; using form values", exc_info=True)
        probed_title = None
        probed_author = None
        probed_language = None
    book_title = _cap_text((title or "") or (probed_title or "") or "Untitled", MAX_TITLE_CHARS) or "Untitled"
    book_author = _cap_text((author or "") or (probed_author or "") or "Unknown", MAX_AUTHOR_CHARS) or "Unknown"
    book_language = _cap_text((language or "") or (probed_language or "") or "en", MAX_LANGUAGE_CHARS) or "en"
    return book_title, book_author, book_language


def _extract_pages_or_raise(
    data: bytes,
    page_start: int,
    page_end: int | None,
    parser: ParserChoice,
    strip_headers: bool,
) -> list[PageText]:
    try:
        return extract_pages(data, page_start, page_end, parser, strip_headers)
    except MaxQualityDisabledError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (ScannedPdfError, EncryptedPdfError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("page extraction failed")
        raise HTTPException(status_code=400, detail=GENERIC_400_DETAIL) from exc


def _detect_chapters_or_raise(
    pages: list[PageText],
    outline: list[OutlineEntry],
    chapter_mode: ChapterModeChoice,
    heuristic_sensitivity: SensitivityChoice,
    min_chapter_chars: int,
    max_chapters: int,
) -> tuple[ChapterSourceChoice, list[Chapter]]:
    try:
        source, chapters = detect_chapters(
            pages,
            outline,
            mode=chapter_mode,
            sensitivity=heuristic_sensitivity,
            min_chars=min_chapter_chars,
            max_chapters=max_chapters,
        )
        return source, chapters  # type: ignore[return-value]
    except NoChaptersError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("chapter detection failed")
        raise HTTPException(status_code=400, detail=GENERIC_400_DETAIL) from exc


def _load_outline_or_raise(data: bytes) -> list[OutlineEntry]:
    try:
        return extract_outline(data)
    except EncryptedPdfError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("outline extraction failed")
        raise HTTPException(status_code=400, detail=GENERIC_400_DETAIL) from exc


def _collect_preview_warnings(
    data: bytes,
    pages: list[PageText],
    parser: ParserChoice,
    include_images: bool,
    include_tables: bool,
    chapter_mode: ChapterModeChoice,
    chapter_source: ChapterSourceChoice,
    page_start: int = 1,
    page_end: int | None = None,
) -> list[str]:
    warnings: list[str] = []
    warnings.extend(detect_mojibake_warnings(pages))
    try:
        _, image_warnings = extract_images(data, include_images, page_start, page_end)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("image extraction for warnings failed")
        raise HTTPException(status_code=400, detail=GENERIC_400_DETAIL) from exc
    warnings.extend(image_warnings)
    try:
        _, table_warnings = extract_all_tables_html(data, parser, include_tables, page_start, page_end)
    except MaxQualityDisabledError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("table extraction for warnings failed")
        raise HTTPException(status_code=400, detail=GENERIC_400_DETAIL) from exc
    warnings.extend(table_warnings)
    if chapter_source == "single":
        warnings.append(SINGLE_FALLBACK_WARNING)
    if chapter_mode == "outline" and chapter_source != "outline":
        warnings.append(f"outline missing or empty; fell back to {chapter_source}")
    return warnings


@pdf_to_epub_router.post("/probe", response_model=PdfProbeResult)
async def probe_pdf_file(file: UploadFile = File(...)) -> PdfProbeResult:
    """Probe a PDF upload and return quick facts for the conversion form."""
    contents = await file.read()
    _ensure_pdf_size(contents)
    _ensure_pdf_magic(contents)
    try:
        probed = await run_in_threadpool(probe_pdf, contents)
    except ScannedPdfError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except EncryptedPdfError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001
        logger.exception("probe failed")
        raise HTTPException(status_code=400, detail=GENERIC_400_DETAIL) from e
    title = _cap_text(probed.metadata.title or "", MAX_TITLE_CHARS) or None
    author = _cap_text(probed.metadata.author or "", MAX_AUTHOR_CHARS) or None
    language = _cap_text(probed.metadata.language or "", MAX_LANGUAGE_CHARS) or None
    gc.collect()
    return PdfProbeResult(
        total_pages=probed.total_pages,
        has_outline=probed.has_outline,
        has_images=probed.has_images,
        metadata=PdfProbeMetadata(
            title=title,
            author=author,
            language=language,
        ),
    )


@pdf_to_epub_router.post("/preview", response_model=PdfPreviewResult)
async def preview_pdf_file(
    file: Annotated[UploadFile, File(...)],
    parser: Annotated[ParserChoice, Form()] = "balanced",
    chapter_mode: Annotated[ChapterModeChoice, Form()] = "auto",
    page_start: Annotated[int, Form()] = 1,
    page_end: Annotated[int | None, Form()] = None,
    heuristic_sensitivity: Annotated[SensitivityChoice, Form()] = "medium",
    min_chapter_chars: Annotated[int, Form()] = 500,
    max_chapters: Annotated[int, Form()] = 300,
    include_images: Annotated[bool, Form()] = True,
    include_tables: Annotated[bool, Form()] = True,
    strip_headers: Annotated[bool, Form()] = True,
    clean_hyphens: Annotated[bool, Form()] = True,
) -> PdfPreviewResult:
    """Preview detected chapters without building the EPUB."""
    contents = await file.read()
    _ensure_pdf_size(contents)
    _ensure_pdf_magic(contents)
    _ensure_parser_enabled(parser)
    pages = await run_in_threadpool(_extract_pages_or_raise, contents, page_start, page_end, parser, strip_headers)
    outline_entries = await run_in_threadpool(_load_outline_or_raise, contents)
    chapter_source, chapters = await run_in_threadpool(
        _detect_chapters_or_raise,
        pages,
        outline_entries,
        chapter_mode,
        heuristic_sensitivity,
        min_chapter_chars,
        max_chapters,
    )
    first_page = pages[0].page_number
    last_page = pages[-1].page_number
    outline_titles = [entry.title for entry in outline_entries if first_page <= entry.start_page <= last_page]
    warnings = await run_in_threadpool(
        _collect_preview_warnings,
        contents,
        pages,
        parser,
        include_images,
        include_tables,
        chapter_mode,
        chapter_source,
        page_start,
        page_end,
    )
    preview_chapters = [_to_preview_chapter(chapter, clean_hyphens) for chapter in chapters]
    gc.collect()
    return PdfPreviewResult(
        chapter_source=chapter_source,
        outline=outline_titles,
        chapters=preview_chapters,
        warnings=warnings,
    )


@pdf_to_epub_router.post("/convert")
async def convert_pdf_file(
    file: Annotated[UploadFile, File(...)],
    parser: Annotated[ParserChoice, Form()] = "balanced",
    chapter_mode: Annotated[ChapterModeChoice, Form()] = "auto",
    page_start: Annotated[int, Form()] = 1,
    page_end: Annotated[int | None, Form()] = None,
    heuristic_sensitivity: Annotated[SensitivityChoice, Form()] = "medium",
    min_chapter_chars: Annotated[int, Form()] = 500,
    max_chapters: Annotated[int, Form()] = 300,
    include_images: Annotated[bool, Form()] = True,
    include_tables: Annotated[bool, Form()] = True,
    strip_headers: Annotated[bool, Form()] = True,
    clean_hyphens: Annotated[bool, Form()] = True,
    title: Annotated[str | None, Form()] = None,
    author: Annotated[str | None, Form()] = None,
    language: Annotated[str | None, Form()] = None,
    use_cover: Annotated[bool, Form()] = True,
    chapter_titles: Annotated[str | None, Form()] = None,
) -> StreamingResponse:
    """Convert a PDF upload to an EPUB blob."""
    contents = await file.read()
    _ensure_pdf_size(contents)
    _ensure_pdf_magic(contents)
    _ensure_parser_enabled(parser)
    pages = await run_in_threadpool(_extract_pages_or_raise, contents, page_start, page_end, parser, strip_headers)
    outline_entries = await run_in_threadpool(_load_outline_or_raise, contents)
    _, chapters = await run_in_threadpool(
        _detect_chapters_or_raise,
        pages,
        outline_entries,
        chapter_mode,
        heuristic_sensitivity,
        min_chapter_chars,
        max_chapters,
    )
    _apply_chapter_title_overrides(chapters, chapter_titles)
    try:
        images, _image_warnings = await run_in_threadpool(
            extract_images, contents, include_images, page_start, page_end
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("image extraction failed")
        raise HTTPException(status_code=400, detail=GENERIC_400_DETAIL) from exc
    try:
        tables_by_page, _table_warnings = await run_in_threadpool(
            extract_all_tables_html, contents, parser, include_tables, page_start, page_end
        )
    except MaxQualityDisabledError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("table extraction failed")
        raise HTTPException(status_code=400, detail=GENERIC_400_DETAIL) from exc
    tables_by_chapter = _map_tables_to_chapters(chapters, tables_by_page)
    book_title, book_author, book_language = await run_in_threadpool(
        _resolve_book_metadata, title, author, language, contents
    )
    effective_chapters = [
        Chapter(
            title=chapter.title,
            text=cleanup_text(chapter.text, clean_hyphens=clean_hyphens),
            start_page=chapter.start_page,
        )
        for chapter in chapters
    ]
    try:
        book, _writer_warnings = await run_in_threadpool(
            build_epub,
            effective_chapters,
            title=book_title,
            author=book_author,
            language=book_language,
            images=images,
            tables_by_chapter=tables_by_chapter,
            use_cover=use_cover,
            min_chars=min_chapter_chars,
            max_chapters=max_chapters,
        )
    except NoChaptersError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("EPUB build failed")
        raise HTTPException(status_code=400, detail=GENERIC_400_DETAIL) from exc
    expected_titles = [link.title for link in book.toc]  # type: ignore[attr-defined]
    buffer = io.BytesIO()
    try:
        await run_in_threadpool(epub.write_epub, buffer, book, {})
    except Exception as exc:  # noqa: BLE001
        logger.exception("EPUB write failed")
        raise HTTPException(status_code=400, detail=GENERIC_400_DETAIL) from exc
    epub_bytes = buffer.getvalue()
    try:
        await run_in_threadpool(roundtrip_validate, epub_bytes, book_title, book_author, expected_titles)
    except AssertionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("EPUB roundtrip validation failed")
        raise HTTPException(status_code=400, detail=GENERIC_400_DETAIL) from exc
    filename = _sanitize_filename(book_title)
    quoted = quote(filename, safe="")
    gc.collect()
    return StreamingResponse(
        io.BytesIO(epub_bytes),
        media_type="application/epub+zip",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\"; filename*=UTF-8''{quoted}"},
    )
