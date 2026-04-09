from piccolo.columns import JSON, Boolean, ForeignKey, Integer, Text, Timestamp
from piccolo.table import Table


class AudiobookBook(Table, tablename="litestar_audiobook_book"):
    uploaded_by = Text(required=True)
    book_title = Text(required=True)
    book_author = Text(required=True)
    chapter_count = Integer(required=True)
    upload_date = Timestamp(required=True)
    custom_book_title = Text(required=False, null=True, default=None)
    custom_book_author = Text(required=False, null=True, default=None)
    deleted = Boolean(required=True, default=False)


class AudiobookChapter(Table, tablename="litestar_audiobook_chapter"):
    book = ForeignKey(references=AudiobookBook)
    queued = Timestamp(required=False, null=True, default=None)
    started_converting = Timestamp(required=False, null=True, default=None)
    chapter_title = Text(required=True)
    chapter_number = Integer(required=True)
    word_count = Integer(required=True)
    sentence_count = Integer(required=True)
    content = Text(required=True)
    minio_object_name = Text(required=False, null=True, default=None)
    audio_settings = JSON(required=False, null=True, default=None)


__all__ = ["AudiobookBook", "AudiobookChapter"]
