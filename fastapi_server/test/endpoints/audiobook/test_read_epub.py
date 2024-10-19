import io
from pathlib import Path

import pytest
from ebooklib import epub
from hypothesis import given
from hypothesis import strategies as st

from src.routes.audiobook.temp_read_epub import combine_text, extract_chapters, extract_metadata


def generate_epub_helper(book_title: str, book_author: str, chapters: dict[str, str]) -> io.BytesIO:
    book = epub.EpubBook()

    # set metadata
    book.set_identifier("id123456")
    book.set_title(book_title)
    book.set_language("en")

    book.add_author(book_author)
    # Why is this needed?
    book.add_author(
        "Danko Bananko",
        file_as="Gospodin Danko Bananko",
        role="ill",
        uid="coauthor",
    )

    # create chapter
    created_chapters = {}
    for chapter_id, (chapter_title, chapter_content) in enumerate(chapters.items(), start=1):
        c1 = epub.EpubHtml(
            file_name=f"chap_{chapter_id:04d}.xhtml",
            title=chapter_title,
            content=chapter_content,
            lang="en",
        )

        # add chapter
        book.add_item(c1)
        created_chapters[chapter_title] = c1

    # See https://github.com/aerkalov/ebooklib/
    # define Table Of Contents
    book.toc = (
        # Why are these extra chapter needed?
        epub.Link("intro.xhtml", "Introduction", "intro"),
        (epub.Section("Languages"), tuple(created_chapters.values())),
    )

    # add default NCX and Nav file
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    book_in_memory = io.BytesIO()
    epub.write_epub(book_in_memory, book, {})
    return book_in_memory


# https://stackoverflow.com/a/57754227/10882657
@given(
    book_title=st.from_regex(r"\w[\w\d\u0370-\u03FF\u0400-\u04FF_ -]*", fullmatch=True),
    book_author=st.from_regex(r"\w[\w\d\u0370-\u03FF\u0400-\u04FF_ -]*", fullmatch=True),
)
def test_epub_reader_extract_metadata(
    book_title: str,
    book_author: str,
):
    epub_book = generate_epub_helper(
        book_title=book_title,
        book_author=book_author,
        chapters={},
    )
    book_metadata = extract_metadata(epub_book)
    assert book_metadata.title == book_title
    assert book_metadata.author == book_author


def test_epub_reader_extract_chapters_simple():
    epub_book = generate_epub_helper(
        book_title="test title",
        book_author="test author",
        chapters={"asd": "asd", "asd2": "asd2"},
    )
    book_chapters = extract_chapters(epub_book)
    assert len(book_chapters) == 2


@given(
    chapters=st.dictionaries(
        # Chapter title
        keys=st.from_regex(r"\w[\w \n]*", fullmatch=True),
        # Chapter content
        values=st.from_regex(r"\w[\w \n]*", fullmatch=True),
        # Alternative parsing if only 1 chapter was detected
        min_size=2,
        max_size=10**4 - 1,
    ),
)
def test_epub_reader_extract_chapters(
    chapters: dict[str, str],
):
    # 2 chapters following each other need to have different text
    chapters = {
        chapter_title: chapter_content
        for (chapter_title, chapter_content), (_chapter_title2, chapter_content2) in zip(
            chapters.items(), list(chapters.items())[1:]
        )
        if chapter_content != chapter_content2
    }
    if len(chapters) < 2:
        return

    epub_book = generate_epub_helper(
        book_title="test title",
        book_author="test author",
        chapters=chapters,
    )

    # Sanity check: Chapter count needs to be the same
    book_chapters = extract_chapters(epub_book)
    assert len(chapters) == len(book_chapters)

    # Check that chapters are identical
    for real_chapter, (expected_chapter_title, expected_chapter_content) in zip(book_chapters, chapters.items()):
        assert real_chapter.chapter_title == expected_chapter_title
        assert real_chapter.combined_text == combine_text([expected_chapter_content])


@pytest.mark.parametrize(
    "book_relative_path, chapters_amount",
    [
        ("actual_books/frankenstein.epub", 31),
        ("actual_books/romeo-and-juliet.epub", 28),
        ("actual_books/the-war-of-the-worlds.epub", 29),
    ],
)
def test_parsing_real_epubs(book_relative_path: str, chapters_amount: int) -> None:  # noqa: F811
    book_path = Path(__file__).parent / book_relative_path
    book_bytes_io = io.BytesIO(book_path.read_bytes())
    chapters_extracted = extract_chapters(book_bytes_io)
    assert len(chapters_extracted) == chapters_amount
