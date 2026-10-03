from __future__ import annotations

import contextlib
import gc
import io
import json
import logging
import tempfile
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import quote

from ebooklib import epub
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

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
    OutlineEntry,
    PageText,
    ScannedPdfError,
    detect_mojibake_warnings,
    extract_images,
    extract_outline,
    extract_pages,
    probe_pdf,
)

pdf_to_epub_router = APIRouter()

logger = logging.getLogger(__name__)

MAX_PDF_SIZE_BYTES = 100 * 1024 * 1024
PREVIEW_CHARS = 500
MAX_TITLE_CHARS = 200
MAX_AUTHOR_CHARS = 200
MAX_LANGUAGE_CHARS = 20
GENERIC_400_DETAIL = "invalid or unreadable PDF"


def _unlink_temp_file(path: str) -> None:
    with contextlib.suppress(OSError, FileNotFoundError):
        Path(path).unlink(missing_ok=True)


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


def _apply_chapter_title_overrides(chapters: list[Chapter], raw: str | None) -> None:
    # WHY in-place override: detected order drives writer TOC.
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
    strip_headers: bool,
) -> list[PageText]:
    try:
        return extract_pages(data, page_start, page_end, strip_headers)
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
    include_images: bool,
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
    if chapter_source == "single":
        warnings.append(SINGLE_FALLBACK_WARNING)
    if chapter_mode == "outline" and chapter_source != "outline":
        warnings.append(f"outline missing or empty; fell back to {chapter_source}")
    return warnings


@pdf_to_epub_router.post("/probe", response_model=PdfProbeResult)
async def probe_pdf_file(file: UploadFile = File(...)) -> PdfProbeResult:
    """Probe a PDF upload and return quick facts for the conversion form."""
    try:
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
    finally:
        with contextlib.suppress(Exception):
            await file.close()
        with contextlib.suppress(NameError, UnboundLocalError):
            del contents
        with contextlib.suppress(NameError, UnboundLocalError):
            del probed
        gc.collect()


@pdf_to_epub_router.post("/preview", response_model=PdfPreviewResult)
async def preview_pdf_file(
    file: Annotated[UploadFile, File(...)],
    chapter_mode: Annotated[ChapterModeChoice, Form()] = "auto",
    page_start: Annotated[int, Form()] = 1,
    page_end: Annotated[int | None, Form()] = None,
    heuristic_sensitivity: Annotated[SensitivityChoice, Form()] = "medium",
    min_chapter_chars: Annotated[int, Form()] = 500,
    max_chapters: Annotated[int, Form()] = 300,
    include_images: Annotated[bool, Form()] = True,
    strip_headers: Annotated[bool, Form()] = True,
    clean_hyphens: Annotated[bool, Form()] = True,
) -> PdfPreviewResult:
    """Preview detected chapters without building the EPUB."""
    try:
        contents = await file.read()
        _ensure_pdf_size(contents)
        _ensure_pdf_magic(contents)
        pages = await run_in_threadpool(_extract_pages_or_raise, contents, page_start, page_end, strip_headers)
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
            include_images,
            chapter_mode,
            chapter_source,
            page_start,
            page_end,
        )
        # WHY lightweight preview: images discarded, only warnings kept;
        # include_images flag still reflected in warnings.
        preview_chapters = [_to_preview_chapter(chapter, clean_hyphens) for chapter in chapters]
        return PdfPreviewResult(
            chapter_source=chapter_source,
            outline=outline_titles,
            chapters=preview_chapters,
            warnings=warnings,
        )
    finally:
        with contextlib.suppress(Exception):
            await file.close()
        with contextlib.suppress(NameError, UnboundLocalError):
            del contents
        with contextlib.suppress(NameError, UnboundLocalError):
            del pages
        with contextlib.suppress(NameError, UnboundLocalError):
            del outline_entries
        with contextlib.suppress(NameError, UnboundLocalError):
            del chapters
        with contextlib.suppress(NameError, UnboundLocalError):
            del warnings
        with contextlib.suppress(NameError, UnboundLocalError):
            del preview_chapters
        with contextlib.suppress(NameError, UnboundLocalError):
            del outline_titles
        gc.collect()


@pdf_to_epub_router.post("/convert")
async def convert_pdf_file(
    file: Annotated[UploadFile, File(...)],
    chapter_mode: Annotated[ChapterModeChoice, Form()] = "auto",
    page_start: Annotated[int, Form()] = 1,
    page_end: Annotated[int | None, Form()] = None,
    heuristic_sensitivity: Annotated[SensitivityChoice, Form()] = "medium",
    min_chapter_chars: Annotated[int, Form()] = 500,
    max_chapters: Annotated[int, Form()] = 300,
    include_images: Annotated[bool, Form()] = True,
    strip_headers: Annotated[bool, Form()] = True,
    clean_hyphens: Annotated[bool, Form()] = True,
    title: Annotated[str | None, Form()] = None,
    author: Annotated[str | None, Form()] = None,
    language: Annotated[str | None, Form()] = None,
    use_cover: Annotated[bool, Form()] = True,
    chapter_titles: Annotated[str | None, Form()] = None,
) -> FileResponse:
    """Convert a PDF upload to an EPUB blob."""
    buffer: io.BytesIO | None = None
    tmp_path: str | None = None
    response_created = False
    try:
        contents = await file.read()
        _ensure_pdf_size(contents)
        _ensure_pdf_magic(contents)
        pages = await run_in_threadpool(_extract_pages_or_raise, contents, page_start, page_end, strip_headers)
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
        # WHY temp file: avoids StreamingResponse(io.BytesIO(epub_bytes)) double-copy;
        # validate from memory then write file, stream from disk via FileResponse.
        with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as tmp:
            tmp.write(epub_bytes)
            tmp.flush()
            tmp_path = tmp.name
        disposition = f"attachment; filename=\"{filename}\"; filename*=UTF-8''{quoted}"
        response_created = True
        return FileResponse(
            path=tmp_path,
            media_type="application/epub+zip",
            filename=filename,
            background=BackgroundTask(_unlink_temp_file, tmp_path),
            headers={"Content-Disposition": disposition},
        )
    finally:
        with contextlib.suppress(Exception):
            await file.close()
        if not response_created and tmp_path is not None:
            with contextlib.suppress(Exception):
                Path(tmp_path).unlink(missing_ok=True)
        if buffer is not None:
            with contextlib.suppress(Exception):
                buffer.close()
        with contextlib.suppress(NameError, UnboundLocalError):
            del contents
        with contextlib.suppress(NameError, UnboundLocalError):
            del pages
        with contextlib.suppress(NameError, UnboundLocalError):
            del outline_entries
        with contextlib.suppress(NameError, UnboundLocalError):
            del chapters
        with contextlib.suppress(NameError, UnboundLocalError):
            del images
        with contextlib.suppress(NameError, UnboundLocalError):
            del effective_chapters
        with contextlib.suppress(NameError, UnboundLocalError):
            del book
        with contextlib.suppress(NameError, UnboundLocalError):
            del buffer
        with contextlib.suppress(NameError, UnboundLocalError):
            del epub_bytes
        gc.collect()
