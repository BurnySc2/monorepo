"""Chapter detection for the pdf_to_epub feature.

Outline-first slicing with heuristic and single-chapter fallbacks plus text
cleanup. Pure-text implementation; layout signals apply when page objects
carry font metadata, otherwise regex/caps/page-break heuristics run.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from components.pdf_to_epub.parser import OutlineEntry, PageText

ChapterMode = Literal["auto", "outline", "heuristic", "single"]
ChapterSource = Literal["outline", "heuristic", "single"]
HeuristicSensitivity = Literal["low", "medium", "high"]

DEFAULT_MIN_CHARS = 500
DEFAULT_MAX_CHAPTERS = 300
SINGLE_CHUNK_CHARS = 50_000
SINGLE_FALLBACK_WARNING = "no chapters detected — single-chapter EPUB"


class NoChaptersError(Exception):
    """Raised when no chapter can be recovered (maps to 422)."""


@dataclass
class Chapter:
    """One detected chapter with 1-based start page."""

    title: str
    text: str
    start_page: int


_LIGATURES: tuple[tuple[str, str], ...] = (
    ("ﬁ", "fi"),
    ("ﬂ", "fl"),
    ("ﬀ", "ff"),
    ("ﬃ", "ffi"),
    ("ﬄ", "ffl"),
    ("ﬅ", "ft"),
    ("ﬆ", "st"),
)

_HYPHEN_BREAK_RE = re.compile(r"(\w)-\s*\n\s*(\w)")
_HYPHEN_SPACE_RE = re.compile(r"(\w)- ([a-z])")
_WHITESPACE_RE = re.compile(r"\s+")

_NUMBERED_HEADING_RE = re.compile(
    r"^(?:chapter|part|section|book|volume)\s+(?:[0-9]+|[ivxlcdm]+|one|two|three|four|five|six|seven|"
    r"eight|nine|ten)\b.*$",
    re.IGNORECASE,
)
_KEYWORD_HEADING_RE = re.compile(
    r"^(?:chapter|part|section|book|volume|prologue|epilogue|appendix)\b.*$", re.IGNORECASE
)
_NUMERIC_HEADING_RE = re.compile(r"^(?:\d{1,3}|[IVXLCDM]{1,6})[.\):\-]\s+\S+.*$")
_STANDALONE_KEYWORDS = frozenset(
    {
        "prologue",
        "epilogue",
        "appendix",
        "introduction",
        "preface",
        "foreword",
        "afterword",
        "interlude",
    }
)


def cleanup_text(text: str, clean_hyphens: bool = True) -> str:
    """Normalize ligatures, join line-break hyphenation, collapse whitespace."""
    if clean_hyphens:
        text = text.replace("­", "")
        text = _HYPHEN_BREAK_RE.sub(r"\1\2", text)
        for source, target in _LIGATURES:
            if source in text:
                text = text.replace(source, target)
    collapsed = _WHITESPACE_RE.sub(" ", text).strip()
    if clean_hyphens and collapsed:
        collapsed = _HYPHEN_SPACE_RE.sub(r"\1\2", collapsed)
    return collapsed


def _normalize_sensitivity(sensitivity: str) -> HeuristicSensitivity:
    normalized = sensitivity.strip().lower()
    if normalized == "med":
        return "medium"
    if normalized in ("low", "medium", "high"):
        return normalized  # type: ignore[return-value]
    raise ValueError(f"unknown sensitivity: {sensitivity}")


def _fallback_title(index: int) -> str:
    return f"Chapter {index}"


def _clean_title(raw: str | None, fallback_index: int) -> str:
    cleaned = (raw or "").strip()
    cleaned = _WHITESPACE_RE.sub(" ", cleaned).strip()
    if not cleaned:
        return _fallback_title(fallback_index)
    return cleaned[:200]


def _is_standalone_keyword(line: str) -> bool:
    lowered = line.strip().lower()
    if lowered in _STANDALONE_KEYWORDS:
        return True
    if len(line) <= 60 and len(line.split()) <= 5:
        first_word = lowered.split(" ", 1)[0] if lowered else ""
        return first_word in _STANDALONE_KEYWORDS
    return False


def _is_caps_heading(line: str) -> bool:
    stripped = line.strip()
    if not 3 <= len(stripped) <= 80:
        return False
    words = stripped.split()
    if len(words) > 12:
        return False
    has_alpha = any(char.isalpha() for char in stripped)
    if not has_alpha:
        return False
    return all(not char.islower() for char in stripped)


def _is_short_title(line: str) -> bool:
    stripped = line.strip()
    if not 2 <= len(stripped) <= 60:
        return False
    words = stripped.split()
    if not 1 <= len(words) <= 8:
        return False
    if stripped.endswith((".", ",", ";", ":")):
        return False
    if not any(char.isalpha() for char in stripped):
        return False
    return stripped[0].isupper()


def _has_layout_signals(page: PageText) -> bool:
    # WHY layout hook: PageText is pure text in T1; later parsers may attach font metadata.
    return any(getattr(page, attr, None) for attr in ("blocks", "spans", "font_sizes", "lines"))


def _is_heading(line: str, sensitivity: HeuristicSensitivity, at_page_start: bool) -> bool:
    stripped = line.strip()
    if len(stripped) < 2 or len(stripped) > 200:
        return False
    if _NUMBERED_HEADING_RE.match(stripped):
        return True
    if sensitivity == "low":
        return False
    if _is_standalone_keyword(stripped):
        return True
    if _is_caps_heading(stripped):
        return True
    if _KEYWORD_HEADING_RE.match(stripped) and len(stripped) <= 120:
        # WHY medium recall: keyword-led lines without numbers still split books.
        return True
    if sensitivity == "high":
        if _NUMERIC_HEADING_RE.match(stripped) and len(stripped) <= 100:
            return True
        if at_page_start and _is_short_title(stripped):
            return True
    return False


def _page_lines(page: PageText) -> list[str]:
    return [line.strip() for line in page.text.splitlines() if line.strip()]


def _detect_heuristic_breaks(pages: list[PageText], sensitivity: HeuristicSensitivity) -> list[tuple[int, int, str]]:
    breaks: list[tuple[int, int, str]] = []
    for page_index, page in enumerate(pages):
        _ = _has_layout_signals(page)
        lines = _page_lines(page)
        for line_index, line in enumerate(lines):
            if _is_heading(line, sensitivity, at_page_start=line_index == 0):
                breaks.append((page_index, line_index, line.strip()[:200]))
    return breaks


def _slice_by_breaks(pages: list[PageText], breaks: list[tuple[int, int, str]]) -> list[Chapter]:
    if not breaks:
        return []
    line_lists = [_page_lines(page) for page in pages]
    ordered = sorted(breaks, key=lambda item: (item[0], item[1]))
    chapters: list[Chapter] = []
    for pos, (page_index, line_index, title) in enumerate(ordered):
        if pos + 1 < len(ordered):
            next_page, next_line, _ = ordered[pos + 1]
        else:
            next_page, next_line = len(pages), 0
        parts: list[str] = []
        for idx in range(page_index, min(next_page + 1, len(pages))):
            lines = line_lists[idx]
            start = line_index if idx == page_index else 0
            end = len(lines)
            if idx == next_page and pos + 1 < len(ordered):
                end = next_line
            parts.extend(lines[start:end])
        text = cleanup_text(" ".join(parts))
        chapters.append(
            Chapter(
                title=_clean_title(title, len(chapters) + 1),
                text=text,
                start_page=pages[page_index].page_number,
            )
        )
    return chapters


def _slice_by_outline(pages: list[PageText], outline: list[OutlineEntry]) -> list[Chapter]:
    if not pages or not outline:
        return []
    first_page = pages[0].page_number
    last_page = pages[-1].page_number
    page_by_number = {page.page_number: page for page in pages}
    sorted_entries = sorted(outline, key=lambda entry: entry.start_page)
    in_range = [entry for entry in sorted_entries if first_page <= entry.start_page <= last_page]
    if not in_range:
        return []
    seen: set[str] = set()
    chapters: list[Chapter] = []
    for pos, entry in enumerate(in_range):
        raw_title = entry.title.strip()
        lowered = raw_title.lower()
        if not raw_title or lowered in seen:
            title = _fallback_title(len(chapters) + 1)
        else:
            title = _clean_title(raw_title, len(chapters) + 1)
            seen.add(lowered)
        end_page = in_range[pos + 1].start_page - 1 if pos + 1 < len(in_range) else last_page
        end_page = max(entry.start_page, min(end_page, last_page))
        parts = [
            page_by_number[number].text for number in range(entry.start_page, end_page + 1) if number in page_by_number
        ]
        text = cleanup_text(" ".join(parts))
        chapters.append(Chapter(title=title, text=text, start_page=entry.start_page))
    return chapters


def _single_fallback(pages: list[PageText]) -> list[Chapter]:
    cleaned = [(page.page_number, cleanup_text(page.text)) for page in pages]
    cleaned = [(number, text) for number, text in cleaned if text]
    if not cleaned:
        return []
    chunks: list[Chapter] = []
    current_parts: list[str] = []
    current_chars = 0
    current_start = cleaned[0][0]
    counter = 1

    def _flush() -> None:
        nonlocal current_parts, current_chars, current_start, counter
        if current_parts:
            chunks.append(
                Chapter(
                    title=_fallback_title(counter),
                    text=cleanup_text(" ".join(current_parts)),
                    start_page=current_start,
                )
            )
            counter += 1
            current_parts = []
            current_chars = 0

    for number, text in cleaned:
        if not current_parts:
            current_start = number
        if current_chars + len(text) + 1 <= SINGLE_CHUNK_CHARS or not current_parts:
            if len(text) > SINGLE_CHUNK_CHARS and not current_parts:
                words = text.split(" ")
                part = ""
                for word in words:
                    if len(part) + len(word) + 1 > SINGLE_CHUNK_CHARS and part:
                        current_parts.append(part)
                        _flush()
                        current_start = number
                        part = word
                    else:
                        part = f"{part} {word}".strip()
                if part:
                    current_parts.append(part)
                    current_chars += len(part)
            else:
                current_parts.append(text)
                current_chars += len(text) + 1
        else:
            _flush()
            current_start = number
            current_parts.append(text)
            current_chars = len(text)
    _flush()
    return chunks


def _merge_small_chapters(chapters: list[Chapter], min_chars: int) -> list[Chapter]:
    if len(chapters) <= 1 or min_chars <= 0:
        return chapters
    merged: list[Chapter] = []
    for chapter in chapters:
        if not merged:
            merged.append(chapter)
            continue
        if len(chapter.text) < min_chars:
            merged[-1].text = cleanup_text(f"{merged[-1].text} {chapter.text}")
        else:
            merged.append(chapter)
    if len(merged) > 1 and len(merged[0].text) < min_chars:
        second = merged.pop(1)
        merged[0].text = cleanup_text(f"{merged[0].text} {second.text}")
        merged[0].start_page = min(merged[0].start_page, second.start_page)
    return merged


def _demote_excess_chapters(chapters: list[Chapter], max_chapters: int) -> list[Chapter]:
    if max_chapters < 1:
        raise ValueError("max_chapters must be >= 1")
    if len(chapters) <= max_chapters:
        return chapters
    indexed = sorted(enumerate(chapters), key=lambda pair: len(pair[1].text), reverse=True)
    keep_positions = sorted(pos for pos, _ in indexed[:max_chapters])
    keep_set = set(keep_positions)
    survivors: dict[int, Chapter] = {pos: chapters[pos] for pos in keep_positions}
    for pos, chapter in enumerate(chapters):
        if pos in keep_set:
            continue
        prev_positions = [keep for keep in keep_positions if keep < pos]
        if prev_positions:
            target = survivors[prev_positions[-1]]
            target.text = cleanup_text(f"{target.text} {chapter.title} {chapter.text}")
        else:
            target_pos = min(keep_positions)
            target = survivors[target_pos]
            target.text = cleanup_text(f"{chapter.title} {chapter.text} {target.text}")
            target.start_page = min(target.start_page, chapter.start_page)
    return [survivors[pos] for pos in keep_positions]


def _apply_limits(chapters: list[Chapter], min_chars: int, max_chapters: int) -> list[Chapter]:
    merged = _merge_small_chapters(chapters, min_chars)
    return _demote_excess_chapters(merged, max_chapters)


def detect_chapters(
    pages: list[PageText],
    outline: list[OutlineEntry] | None = None,
    mode: ChapterMode = "auto",
    sensitivity: str = "medium",
    min_chars: int = DEFAULT_MIN_CHARS,
    max_chapters: int = DEFAULT_MAX_CHAPTERS,
) -> tuple[ChapterSource, list[Chapter]]:
    """Detect chapters, never returning an empty list silently."""
    if not pages:
        raise NoChaptersError("no chapters recoverable: empty document")
    if any(not isinstance(page.text, str) for page in pages):
        raise NoChaptersError("no chapters recoverable: unreadable pages")
    if all(not page.text.strip() for page in pages):
        raise NoChaptersError("no chapters recoverable: empty document")
    if min_chars < 0:
        raise ValueError("min_chars must be >= 0")
    if max_chapters < 1:
        raise ValueError("max_chapters must be >= 1")
    if mode not in ("auto", "outline", "heuristic", "single"):
        raise ValueError(f"unknown chapter mode: {mode}")
    tuned = _normalize_sensitivity(sensitivity)
    entries = list(outline) if outline else []

    def _outline_result() -> tuple[ChapterSource, list[Chapter]] | None:
        if not entries:
            return None
        sliced = _slice_by_outline(pages, entries)
        if not sliced:
            return None
        return ("outline", _apply_limits(sliced, min_chars, max_chapters))

    def _heuristic_result() -> tuple[ChapterSource, list[Chapter]] | None:
        breaks = _detect_heuristic_breaks(pages, tuned)
        if not breaks:
            return None
        sliced = _slice_by_breaks(pages, breaks)
        if not sliced or all(not chapter.text for chapter in sliced):
            return None
        return ("heuristic", _apply_limits(sliced, min_chars, max_chapters))

    def _single_result() -> tuple[ChapterSource, list[Chapter]]:
        sliced = _apply_limits(_single_fallback(pages), min_chars, max_chapters)
        if not sliced or all(not chapter.text for chapter in sliced):
            raise NoChaptersError("no chapters recoverable: empty document")
        return ("single", sliced)

    if mode == "single":
        return _single_result()
    if mode == "outline":
        outlined = _outline_result()
        if outlined is not None:
            return outlined
        heuristic = _heuristic_result()
        if heuristic is not None:
            return heuristic
        return _single_result()
    if mode == "heuristic":
        heuristic = _heuristic_result()
        if heuristic is not None:
            return heuristic
        return _single_result()
    outlined = _outline_result()
    if outlined is not None:
        return outlined
    heuristic = _heuristic_result()
    if heuristic is not None:
        return heuristic
    return _single_result()
