import io
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

import nltk  # pyre-fixme[21]
from bs4 import BeautifulSoup  # pyre-fixme[21]
from ebooklib import ITEM_DOCUMENT  # pyre-fixme[21]
from ebooklib.epub import EpubHtml, EpubReader, Link, Section  # pyre-fixme[21]
from loguru import logger
from nltk import word_tokenize
from nltk.tokenize import sent_tokenize  # pyre-fixme[21]

nltk.download("punkt_tab")


def extract_sentences(text: str) -> list[str]:
    sentences = sent_tokenize(text)
    return sentences


@dataclass
class EpubChapter:
    chapter_title: str
    chapter_number: int
    word_count: int
    sentence_count: int
    content: list[str]
    combined_text: str


def extract_chapters(data: io.BytesIO) -> list[EpubChapter]:
    c = EpubReader("")
    c.zf = zipfile.ZipFile(data)
    c._load_container()
    c._load_opf_file()
    prev_text = ""
    chapters = []
    chapter_number = 1

    # pyre-fixme[11]
    def follow_link(chapter: Link | Section | EpubHtml):
        nonlocal chapter_number, prev_text
        if isinstance(chapter, list | tuple):
            for section in chapter:
                follow_link(section)
            return
        if isinstance(chapter, Section):
            # Not relevant
            return
        if not isinstance(chapter, Link | EpubHtml):
            # Discard all other types
            logger.debug(f"Was type: {type(chapter)}")
            return
        if isinstance(chapter, EpubHtml):
            epub_html: EpubHtml = chapter
            chapter_title = epub_html.id
        else:
            epub_html: EpubHtml = c.book.get_item_with_href(chapter.href.split("#")[0])
            chapter_title = chapter.title
            # Might be missing in some books
            if epub_html is None:
                return
        if epub_html.get_type() != ITEM_DOCUMENT:
            return

        # Parse the HTML content
        soup = BeautifulSoup(epub_html.get_body_content(), "html.parser")

        for span in soup.find_all("span"):
            # Seems to do the same as replace_with(span.text)
            # span.unwrap()
            span.replace_with(span.text.strip().strip("\n"))

        # TODO Remove <a> and <img> to remove texts describing images?

        chapter_text = soup.get_text()
        texts = [row for row in chapter_text.split("\n") if row.strip() != ""]

        # Combine text for word count, sentence count
        combined_text = " ".join(row for row in texts)
        combined_text = re.sub(r"\s+", " ", combined_text)
        if combined_text != "" and combined_text != prev_text:
            chapters.append(
                EpubChapter(
                    chapter_title=chapter_title,
                    chapter_number=chapter_number,
                    word_count=len(word_tokenize(combined_text)),
                    sentence_count=len(extract_sentences(combined_text)),
                    content=texts,
                    combined_text=combined_text,
                )
            )
            chapter_number += 1
            prev_text = combined_text

    for chapter in c.book.toc:
        follow_link(chapter)

    # If chapters are empty (= no text extracted), try to find text via c.book.items
    # Assumption: was created with callibre
    if len(chapters) <= 1:
        for chapter in c.book.items:
            follow_link(chapter)

    return chapters


@dataclass
class EpubMetadata:
    title: str
    language: str
    author: str
    date: str
    # Publisher?
    identifier: str


def extract_metadata(data: io.BytesIO) -> EpubMetadata:
    c = EpubReader("")
    c.zf = zipfile.ZipFile(data)
    c._load_container()
    c._load_opf_file()  # load title and toc etc
    title = c.book.get_metadata("DC", "title")[0][0]
    creator = c.book.get_metadata("DC", "creator")[0][0]
    identifier = c.book.get_metadata("DC", "identifier")[0][0]
    # Some books seem to have no date set
    date = ""
    if c.book.get_metadata("DC", "date") != []:
        date = c.book.get_metadata("DC", "date")[0][0]
    language = c.book.get_metadata("DC", "language")[0][0]
    return EpubMetadata(
        title=title,
        language=language,
        author=creator,
        # Date seems to be upload date?
        date=date,
        identifier=identifier,
    )


if __name__ == "__main__":
    # Extract metadata
    path = Path("/home/burny/Downloads/pg67979-images-3.epub")
    with path.open("rb") as f:
        data = f.read()
        data = io.BytesIO(data)

    meta = extract_metadata(data)
    info = extract_chapters(data)
