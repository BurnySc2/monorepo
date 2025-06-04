import asyncio
import arrow
from piccolo.columns import ForeignKey, Integer, Text, Timestamptz, Boolean, JSON
from piccolo.table import Table



# await AudiobookBook.create_table(if_not_exists=True)
# await AudiobookChapter.create_table(if_not_exists=True)
class AudiobookBook(Table, tablename="litestar_audiobook_book"):
    uploaded_by = Text(required=True)
    book_title = Text(required=True)
    book_author = Text(required=True)
    chapter_count = Integer(required=True)
    upload_date = Timestamptz(default=arrow.utcnow().datetime)
    custom_book_title = Text()
    custom_book_author = Text()
    # Soft delete flag
    deleted = Boolean(default=False)


class AudiobookChapter(Table, tablename="litestar_audiobook_chapter"):
    book = ForeignKey(references=AudiobookBook)
    queued = Timestamptz()
    started_converting = Timestamptz()
    chapter_title = Text(required=True)
    chapter_number = Integer(required=True)
    word_count = Integer(required=True)
    sentence_count = Integer(required=True)
    content = Text(required=True)
    minio_object_name = Text()
    audio_settings = JSON()

