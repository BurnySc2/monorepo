"""PDF parser for the pdf_to_epub feature.

Probe via pypdf plus page text extraction with page-range slicing and
repeated header/footer filtering. Images come from pypdf XObjects with
Pillow downscaling; mojibake surfaces as warnings, never failures.
"""

from __future__ import annotations

import contextlib
import gc
import hashlib
import io
import statistics
from collections import Counter
from dataclasses import dataclass

from PIL import Image
from pypdf import PdfReader


class ScannedPdfError(Exception):
    """Raised when a PDF has no usable text layer."""


class EncryptedPdfError(Exception):
    """Raised when a PDF requires a password to open."""


@dataclass
class PageText:
    """One page of extracted text with 1-based page number."""

    page_number: int
    text: str


@dataclass
class OutlineEntry:
    """One outline entry with 1-based start page."""

    title: str
    start_page: int


@dataclass
class ContentFlags:
    """Content signals for one document. Stub for T2 preview/convert."""

    has_images: bool = False
    has_outline: bool = False
    has_text: bool = False


@dataclass
class PdfMetadata:
    title: str | None
    author: str | None
    language: str | None


@dataclass
class PdfProbeResult:
    total_pages: int
    has_outline: bool
    has_images: bool
    metadata: PdfMetadata


SCANNED_CHARS_THRESHOLD = 50
PROBE_SAMPLE_PAGES = 5
PROBE_FULL_SCAN_PAGES = 10


def _normalize_optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _extract_language(reader: PdfReader) -> str | None:
    try:
        catalog = reader.root_object
        raw = catalog.get("/Lang")
    except Exception:  # noqa: BLE001
        return None
    if raw is None:
        return None
    normalized = _normalize_optional_text(raw)
    if normalized is None:
        return None
    return normalized.strip("/() \t\r\n") or None


def _extract_metadata(reader: PdfReader) -> PdfMetadata:
    info = reader.metadata
    title = _normalize_optional_text(info.title) if info is not None else None
    author = _normalize_optional_text(info.author) if info is not None else None
    language = _extract_language(reader)
    return PdfMetadata(title=title, author=author, language=language)


def _has_outline(reader: PdfReader) -> bool:
    try:
        outline = reader.outline
    except Exception:  # noqa: BLE001
        return False
    return bool(outline)


def _page_has_image(page: object) -> bool:
    try:
        resources = page.get("/Resources")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        return False
    if resources is None:
        return False
    get_object = getattr(resources, "get_object", None)
    if callable(get_object):
        try:
            resources = get_object()
        except Exception:  # noqa: BLE001
            return False
    if not isinstance(resources, dict):
        return False
    xobjects = resources.get("/XObject")
    if xobjects is None:
        return False
    get_xobject = getattr(xobjects, "get_object", None)
    if callable(get_xobject):
        try:
            xobjects = get_xobject()
        except Exception:  # noqa: BLE001
            return False
    if not isinstance(xobjects, dict):
        return False
    for key in list(xobjects.keys()):
        entry = xobjects[key]
        get_entry = getattr(entry, "get_object", None)
        if callable(get_entry):
            try:
                entry = get_entry()
            except Exception:  # noqa: BLE001
                continue
        if isinstance(entry, dict) and entry.get("/Subtype") == "/Image":
            return True
    return False


def _has_images(reader: PdfReader) -> bool:
    return any(_page_has_image(page) for page in reader.pages)


def _sample_indices(total_pages: int) -> list[int]:
    if total_pages <= PROBE_FULL_SCAN_PAGES:
        return list(range(total_pages))
    last = total_pages - 1
    return [0, total_pages // 4, total_pages // 2, (3 * total_pages) // 4, last]


def _page_text_length(reader: PdfReader, index: int) -> int:
    try:
        text = reader.pages[index].extract_text() or ""
    except Exception:  # noqa: BLE001
        return 0
    return len(text.strip())


def _median_text_chars(reader: PdfReader, total_pages: int) -> float:
    indices = _sample_indices(total_pages)
    lengths = [_page_text_length(reader, index) for index in indices]
    if not lengths:
        return 0.0
    return float(statistics.median(lengths))


def probe_pdf(data: bytes) -> PdfProbeResult:
    """Return quick facts for a PDF, rejecting encrypted and scanned files."""
    stream = io.BytesIO(data)
    reader = PdfReader(stream)
    try:
        if reader.is_encrypted:
            raise EncryptedPdfError("encrypted PDF; password-protected files are not supported")
        total_pages = len(reader.pages)
        if total_pages == 0:
            raise ScannedPdfError("no extractable text found; scanned PDFs are not supported")
        has_outline = _has_outline(reader)
        has_images = _has_images(reader)
        metadata = _extract_metadata(reader)
        median_chars = _median_text_chars(reader, total_pages)
        if median_chars < SCANNED_CHARS_THRESHOLD:
            raise ScannedPdfError("no extractable text found; scanned PDFs are not supported")
        return PdfProbeResult(
            total_pages=total_pages,
            has_outline=has_outline,
            has_images=has_images,
            metadata=metadata,
        )
    finally:
        del reader
        with contextlib.suppress(Exception):
            stream.close()
        gc.collect()


def _flatten_outline(reader: PdfReader, items: list[object], out: list[OutlineEntry]) -> None:
    for item in items:
        if isinstance(item, list):
            _flatten_outline(reader, item, out)
            continue
        title = str(getattr(item, "title", "") or "").strip()
        try:
            page_index = reader.get_destination_page_number(item)  # type: ignore[arg-type]
        except Exception:  # noqa: BLE001
            page_index = None
        if page_index is None:
            continue
        out.append(OutlineEntry(title=title, start_page=int(page_index) + 1))


def extract_outline(data: bytes) -> list[OutlineEntry]:
    """Return flattened outline entries with 1-based start pages."""
    stream = io.BytesIO(data)
    reader = PdfReader(stream)
    try:
        if reader.is_encrypted:
            raise EncryptedPdfError("encrypted PDF; password-protected files are not supported")
        try:
            raw_outline = reader.outline
        except Exception:  # noqa: BLE001
            return []
        if not raw_outline:
            return []
        entries: list[OutlineEntry] = []
        _flatten_outline(reader, list(raw_outline), entries)
        return sorted(entries, key=lambda entry: entry.start_page)
    finally:
        del reader
        with contextlib.suppress(Exception):
            stream.close()
        gc.collect()


def _validate_page_range(total_pages: int, page_start: int, page_end: int | None) -> tuple[int, int]:
    start = page_start if page_start >= 1 else 1
    end = total_pages if page_end is None else page_end
    if page_start < 1 or (page_end is not None and page_end < 1):
        raise ValueError("page_start and page_end are 1-based and must be >= 1")
    if start > total_pages or end < 1:
        raise ValueError("page range is outside the document")
    start = max(1, min(start, total_pages))
    end = max(1, min(end, total_pages))
    if start > end:
        raise ValueError("page_start must be <= page_end")
    return start, end


def _extract_text_pypdf(reader: PdfReader, index: int) -> str:
    try:
        return reader.pages[index].extract_text() or ""
    except Exception:  # noqa: BLE001
        return ""


def _extract_texts_pypdf(data: bytes, indices: list[int]) -> list[str]:
    stream = io.BytesIO(data)
    reader = PdfReader(stream)
    try:
        return [_extract_text_pypdf(reader, index) for index in indices]
    finally:
        del reader
        with contextlib.suppress(Exception):
            stream.close()
        gc.collect()


def _first_non_empty_line(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def _last_non_empty_line(text: str) -> str | None:
    for line in reversed(text.splitlines()):
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def _strip_repeated_headers(texts: list[str]) -> list[str]:
    """Drop identical first/last lines seen on >= 80% of pages."""
    total = len(texts)
    if total < 3:
        return texts
    first_lines = [_first_non_empty_line(text) for text in texts]
    last_lines = [_last_non_empty_line(text) for text in texts]
    header: str | None = None
    footer: str | None = None
    first_counts = Counter(line for line in first_lines if line is not None)
    if first_counts:
        top_line, top_count = first_counts.most_common(1)[0]
        if top_count >= 0.8 * total:
            header = top_line
    last_counts = Counter(line for line in last_lines if line is not None)
    if last_counts:
        top_line, top_count = last_counts.most_common(1)[0]
        if top_count >= 0.8 * total:
            footer = top_line
    if header is None and footer is None:
        return texts
    stripped: list[str] = []
    for text in texts:
        lines = text.splitlines()
        if header is not None:
            for pos, line in enumerate(lines):
                if line.strip():
                    if line.strip() == header:
                        lines.pop(pos)
                    break
        if footer is not None:
            for pos in range(len(lines) - 1, -1, -1):
                if lines[pos].strip():
                    if lines[pos].strip() == footer:
                        lines.pop(pos)
                    break
        stripped.append("\n".join(lines))
    return stripped


def extract_pages(
    data: bytes,
    page_start: int = 1,
    page_end: int | None = None,
    strip_headers: bool = True,
) -> list[PageText]:
    """Extract page texts for a 1-based inclusive range with header filtering."""
    stream = io.BytesIO(data)
    reader = PdfReader(stream)
    try:
        if reader.is_encrypted:
            raise EncryptedPdfError("encrypted PDF; password-protected files are not supported")
        total_pages = len(reader.pages)
        if total_pages == 0:
            raise ScannedPdfError("no extractable text found; scanned PDFs are not supported")
        start, end = _validate_page_range(total_pages, page_start, page_end)
        indices = list(range(start - 1, end))
        page_numbers = list(range(start, end + 1))
    finally:
        del reader
        with contextlib.suppress(Exception):
            stream.close()
        gc.collect()
    raw_texts = _extract_texts_pypdf(data, indices)
    if strip_headers:
        raw_texts = _strip_repeated_headers(raw_texts)
    pages = [PageText(page_number=number, text=text) for number, text in zip(page_numbers, raw_texts, strict=True)]
    usable = [len(page.text.strip()) for page in pages]
    if not usable or max(usable) == 0:
        raise ScannedPdfError("no extractable text found; scanned PDFs are not supported")
    median_chars = float(statistics.median(usable))
    if median_chars < SCANNED_CHARS_THRESHOLD and max(usable) < SCANNED_CHARS_THRESHOLD:
        raise ScannedPdfError("no extractable text found; scanned PDFs are not supported")
    gc.collect()
    return pages


MAX_IMAGE_WIDTH = 1200
IMAGE_JPEG_QUALITY = 70
MAX_IMAGES = 200
MAX_IMAGE_BYTES = 2 * 1024 * 1024


@dataclass
class ExtractedImage:
    """One deduped raster image ready to embed as JPEG."""

    file_name: str
    data: bytes
    media_type: str
    width: int
    height: int
    page_number: int | None


def _image_content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _pil_to_jpeg_bytes(pil_image: Image.Image) -> tuple[bytes, int, int]:
    # WHY cap width: bounds EPUB size while keeping e-reader readability.
    image = pil_image
    if image.mode in ("RGBA", "LA", "PA"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        alpha = image.split()[-1] if image.mode != "P" else None
        if alpha is not None:
            background.paste(image.convert("RGB"), mask=alpha)
            image = background
        else:
            image = image.convert("RGB")
    elif image.mode != "RGB":
        image = image.convert("RGB")
    width, height = image.size
    if width > MAX_IMAGE_WIDTH:
        scaled_height = max(1, int(height * MAX_IMAGE_WIDTH / width))
        # pyrefly: ignore[missing-attribute]
        image = image.resize((MAX_IMAGE_WIDTH, scaled_height), Image.Resampling.LANCZOS)
        width, height = image.size
    buffer = io.BytesIO()
    try:
        image.save(buffer, format="JPEG", quality=IMAGE_JPEG_QUALITY, optimize=True)
        jpeg_bytes = buffer.getvalue()
        return jpeg_bytes, width, height
    finally:
        with contextlib.suppress(Exception):
            buffer.close()


def _decode_xobject_as_pil(entry: object) -> Image.Image | None:
    decode_as_image = getattr(entry, "decode_as_image", None)
    if callable(decode_as_image):
        try:
            decoded = decode_as_image()
            if isinstance(decoded, Image.Image):
                return decoded
        except Exception:  # noqa: BLE001
            pass
    get_data = getattr(entry, "get_data", None)
    if callable(get_data):
        try:
            raw = get_data()
            if isinstance(raw, bytes) and raw:
                stream = io.BytesIO(raw)
                try:
                    with Image.open(stream) as opened:
                        return opened.copy()
                finally:
                    with contextlib.suppress(Exception):
                        stream.close()
        except Exception:  # noqa: BLE001
            pass
    try:
        width = int(entry.get("/Width", 0)) if isinstance(entry, dict) else 0  # type: ignore[union-attr]
        height = int(entry.get("/Height", 0)) if isinstance(entry, dict) else 0  # type: ignore[union-attr]
        raw_candidate: object = get_data() if callable(get_data) else b""
        if not isinstance(raw_candidate, bytes):
            return None
        raw_bits = raw_candidate
        if width > 0 and height > 0 and raw_bits:
            color_space = str(entry.get("/ColorSpace", "/DeviceRGB")) if isinstance(entry, dict) else ""  # type: ignore[union-attr]  # noqa: E501
            mode = "CMYK" if "CMYK" in color_space else ("L" if "Gray" in color_space else "RGB")
            expected = width * height * len(mode)
            if len(raw_bits) >= expected:
                return Image.frombytes(mode, (width, height), raw_bits[:expected]).convert("RGB")
    except Exception:  # noqa: BLE001
        return None
    return None


def _iter_image_entries(reader: PdfReader) -> list[tuple[int, object]]:
    found: list[tuple[int, object]] = []
    for page_index, page in enumerate(reader.pages):
        try:
            resources = page.get("/Resources")  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            continue
        if resources is None:
            continue
        get_object = getattr(resources, "get_object", None)
        if callable(get_object):
            try:
                resources = get_object()
            except Exception:  # noqa: BLE001
                continue
        if not isinstance(resources, dict):
            continue
        xobjects = resources.get("/XObject")
        if xobjects is None:
            continue
        get_xobject = getattr(xobjects, "get_object", None)
        if callable(get_xobject):
            try:
                xobjects = get_xobject()
            except Exception:  # noqa: BLE001
                continue
        if not isinstance(xobjects, dict):
            continue
        for key in list(xobjects.keys()):
            entry = xobjects[key]
            get_entry = getattr(entry, "get_object", None)
            if callable(get_entry):
                try:
                    entry = get_entry()
                except Exception:  # noqa: BLE001
                    continue
            if isinstance(entry, dict) and entry.get("/Subtype") == "/Image":
                found.append((page_index + 1, entry))
    return found


def extract_images(
    data: bytes, include_images: bool = True, page_start: int = 1, page_end: int | None = None
) -> tuple[list[ExtractedImage], list[str]]:
    """Extract raster images as capped JPEGs with hash dedupe; never raises for image faults."""
    warnings: list[str] = []
    if not include_images:
        return [], warnings
    stream: io.BytesIO | None = None
    try:
        stream = io.BytesIO(data)
        reader = PdfReader(stream)
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"images skipped: unreadable PDF ({exc})")
        if stream is not None:
            with contextlib.suppress(Exception):
                stream.close()
        return [], warnings
    try:
        if reader.is_encrypted:
            warnings.append("images skipped: encrypted PDF")
            return [], warnings
        entries = _iter_image_entries(reader)
        total_pages = len(reader.pages)
    finally:
        with contextlib.suppress(UnboundLocalError, NameError):
            del reader
        if stream is not None:
            with contextlib.suppress(Exception):
                stream.close()
        gc.collect()
    if total_pages == 0:
        return [], warnings
    start, end = _validate_page_range(total_pages, page_start, page_end)
    entries = [(page_number, entry) for page_number, entry in entries if start <= page_number <= end]
    # WHY two-phase: decode entry dicts to PIL copies immediately, then release
    # pypdf dicts before heavy JPEG resize/encode work.
    decoded: list[tuple[int, Image.Image]] = []
    skipped_unreadable = 0
    for page_number, entry in entries:
        pil_image = _decode_xobject_as_pil(entry)
        if pil_image is None:
            skipped_unreadable += 1
            warnings.append(f"skipped unreadable image on page {page_number}")
            continue
        decoded.append((page_number, pil_image))
    # Release entry dicts (bytes already copied into PIL) before heavy Pillow work.
    del entries
    with contextlib.suppress(NameError):
        del entry  # type: ignore[has-type]
    gc.collect()
    images: list[ExtractedImage] = []
    seen_hashes: set[str] = set()
    skipped_oversize = 0
    for page_number, pil_image in decoded:
        try:
            jpeg_bytes, width, height = _pil_to_jpeg_bytes(pil_image)
        except Exception:  # noqa: BLE001
            skipped_unreadable += 1
            warnings.append(f"skipped unreadable image on page {page_number}")
            continue
        finally:
            with contextlib.suppress(Exception):
                pil_image.close()
        if len(jpeg_bytes) > MAX_IMAGE_BYTES:
            skipped_oversize += 1
            warnings.append(f"skipped oversized image on page {page_number} (over 2 MB JPEG)")
            continue
        digest = _image_content_hash(jpeg_bytes)
        if digest in seen_hashes:
            continue
        seen_hashes.add(digest)
        if len(images) >= MAX_IMAGES:
            warnings.append(f"skipped image on page {page_number} (over {MAX_IMAGES} image cap)")
            continue
        file_name = f"images/img_{len(images) + 1:04d}.jpg"
        images.append(
            ExtractedImage(
                file_name=file_name,
                data=jpeg_bytes,
                media_type="image/jpeg",
                width=width,
                height=height,
                page_number=page_number,
            )
        )
    del decoded
    with contextlib.suppress(NameError):
        del pil_image  # type: ignore[has-type]
    gc.collect()
    return images, warnings


_MOJIBAKE_MARKERS = ("�", "Ã©", "Ã¨", "Ãª", "Ã´", "Ã±", "â€", "Â ", "Ã ", "ðŸ", "\ufffd")


def _contains_mojibake(text: str) -> bool:
    return any(marker in text for marker in _MOJIBAKE_MARKERS)


def detect_mojibake_warnings(pages: list[PageText]) -> list[str]:
    """Report custom-encoding mojibake per page; conversion still completes."""
    warnings: list[str] = []
    for page in pages:
        if _contains_mojibake(page.text):
            warnings.append(f"possible encoding issues on page {page.page_number}: text may contain mojibake")
    return warnings
