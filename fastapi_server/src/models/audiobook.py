from piccolo.columns import JSON, Boolean, ForeignKey, Integer, Text, Timestamptz
from piccolo.table import Table


# await AudiobookBook.create_table(if_not_exists=True)
# await AudiobookChapter.create_table(if_not_exists=True)
class AudiobookBook(Table, tablename="litestar_audiobook_book"):
    uploaded_by = Text(required=True)
    book_title = Text(required=True)
    book_author = Text(required=True)
    chapter_count = Integer(required=True)
    upload_date = Timestamptz(required=True)
    custom_book_title = Text(required=False)
    custom_book_author = Text(required=False)
    # Soft delete flag
    deleted = Boolean(required=True, default=False)


class AudiobookChapter(Table, tablename="litestar_audiobook_chapter"):
    book = ForeignKey(references=AudiobookBook)
    queued = Timestamptz(required=False)
    started_converting = Timestamptz(required=False)
    chapter_title = Text(required=True)
    chapter_number = Integer(required=True)
    word_count = Integer(required=True)
    sentence_count = Integer(required=True)
    content = Text(required=True)
    minio_object_name = Text(required=False)
    audio_settings = JSON(required=False)
