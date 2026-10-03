from pathlib import Path

import pytest

from components.pdf_to_epub.chapters import (
    SINGLE_FALLBACK_WARNING,
    NoChaptersError,
    cleanup_text,
    detect_chapters,
)
from components.pdf_to_epub.parser import (
    MaxQualityDisabledError,
    OutlineEntry,
    PageText,
    extract_pages,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _long_body(word: str = "body", repeats: int = 200) -> str:
    return " ".join([word] * repeats)


def _pages_numbered(count: int = 3) -> list[PageText]:
    return [
        PageText(page_number=index + 1, text=f"Chapter {index + 1}\n{_long_body(f'word{index}', 200)}")
        for index in range(count)
    ]


def test_outline_driven_slice() -> None:
    pages = _pages_numbered(3)
    outline = [
        OutlineEntry(title="Chapter 1", start_page=1),
        OutlineEntry(title="Chapter 2", start_page=2),
        OutlineEntry(title="", start_page=3),
    ]
    source, chapters = detect_chapters(pages, outline, mode="auto")
    assert source == "outline"
    assert len(chapters) == 3
    assert chapters[0].title == "Chapter 1"
    assert chapters[0].start_page == 1
    assert chapters[2].title == "Chapter 3"
    assert all(len(chapter.text) >= 500 for chapter in chapters)


def test_outline_duplicate_titles_fallback() -> None:
    pages = _pages_numbered(2)
    outline = [
        OutlineEntry(title="Intro", start_page=1),
        OutlineEntry(title="Intro", start_page=2),
    ]
    source, chapters = detect_chapters(pages, outline, mode="outline")
    assert source == "outline"
    assert len(chapters) == 2
    assert chapters[0].title == "Intro"
    assert chapters[1].title == "Chapter 2"


def test_heuristic_no_outline_detects_numbered() -> None:
    pages = _pages_numbered(2)
    source, chapters = detect_chapters(pages, None, mode="auto", sensitivity="low")
    assert source == "heuristic"
    assert len(chapters) == 2
    assert chapters[0].title.lower().startswith("chapter 1")


def test_heuristic_sensitivity_tunable_caps() -> None:
    pages = [
        PageText(page_number=1, text=f"THE BEGINNING\n{_long_body('story', 200)}"),
        PageText(page_number=2, text=f"THE MIDDLE\n{_long_body('tale', 200)}"),
    ]
    low_source, low_chapters = detect_chapters(pages, None, mode="heuristic", sensitivity="low")
    assert low_source == "single"
    assert len(low_chapters) == 1
    med_source, med_chapters = detect_chapters(pages, None, mode="heuristic", sensitivity="medium")
    assert med_source == "heuristic"
    assert len(med_chapters) == 2
    high_source, _ = detect_chapters(pages, None, mode="heuristic", sensitivity="high")
    assert high_source == "heuristic"
    med_short_source, _ = detect_chapters(pages, None, mode="heuristic", sensitivity="med")
    assert med_short_source == "heuristic"


def test_single_fallback_with_warning() -> None:
    pages = [
        PageText(page_number=1, text=_long_body("plain", 300)),
        PageText(page_number=2, text=_long_body("prose", 300)),
    ]
    source, chapters = detect_chapters(pages, None, mode="auto")
    assert source == "single"
    assert len(chapters) >= 1
    assert SINGLE_FALLBACK_WARNING
    assert "single-chapter" in SINGLE_FALLBACK_WARNING


def test_single_mode_long_book_splits() -> None:
    big = "word " * 60000
    pages = [PageText(page_number=1, text=big)]
    source, chapters = detect_chapters(pages, None, mode="single")
    assert source == "single"
    assert len(chapters) > 1
    assert all(chapter.title.startswith("Chapter ") for chapter in chapters)


def test_min_chars_merges_small_fragment() -> None:
    pages = [
        PageText(page_number=1, text=f"Chapter 1\n{_long_body('alpha', 200)}"),
        PageText(page_number=2, text="Chapter 2\ntiny"),
        PageText(page_number=3, text=f"Chapter 3\n{_long_body('beta', 200)}"),
    ]
    _, chapters = detect_chapters(pages, None, mode="heuristic", min_chars=500)
    assert len(chapters) == 2
    assert all(len(chapter.text) >= 500 for chapter in chapters)


def test_max_chapters_demotes_excess() -> None:
    pages = _pages_numbered(5)
    _, chapters = detect_chapters(pages, None, mode="heuristic", min_chars=10, max_chapters=2)
    assert len(chapters) == 2


def test_never_silent_zero_raises() -> None:
    with pytest.raises(NoChaptersError):
        detect_chapters([], None, mode="auto")
    with pytest.raises(NoChaptersError):
        detect_chapters([PageText(page_number=1, text="   \n  ")], None, mode="auto")
    with pytest.raises(NoChaptersError):
        detect_chapters([PageText(page_number=1, text="")], None, mode="single")


def test_cleanup_text_hyphens_ligatures_whitespace() -> None:
    assert cleanup_text("ex- ample") == "example"
    assert cleanup_text("ex-\nample") == "example"
    assert "ﬁ" not in cleanup_text("ﬁle ﬂow")
    assert cleanup_text("ﬁle ﬂow") == "file flow"
    assert cleanup_text("a   \n  b") == "a b"
    assert cleanup_text("well-known", clean_hyphens=True) == "well-known"


def test_extract_pages_range_and_minimal() -> None:
    data = (FIXTURES / "small_text.pdf").read_bytes()
    pages = extract_pages(data, page_start=1, page_end=2, parser="minimal")
    assert len(pages) == 2
    assert pages[0].page_number == 1
    single = extract_pages(data, page_start=2, page_end=2, parser="minimal")
    assert len(single) == 1
    assert single[0].page_number == 2


def test_extract_pages_strip_headers_drops_repeated() -> None:
    data = (FIXTURES / "small_text.pdf").read_bytes()
    pages = extract_pages(data, parser="minimal", strip_headers=True)
    assert len(pages) == 2


def test_extract_pages_max_quality_disabled() -> None:
    data = (FIXTURES / "small_text.pdf").read_bytes()
    with pytest.raises(MaxQualityDisabledError):
        extract_pages(data, parser="max_quality")


def test_extract_pages_invalid_range_rejected() -> None:
    data = (FIXTURES / "small_text.pdf").read_bytes()
    with pytest.raises(ValueError):
        extract_pages(data, page_start=3, page_end=2, parser="minimal")
