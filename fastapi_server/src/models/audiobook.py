from piccolo.columns import ForeignKey, Integer, Text, Timestamptz, Boolean, JSON
from piccolo.table import Table


# await AudiobookBook.create_table(if_not_exists=True)
# await AudiobookChapter.create_table(if_not_exists=True)
class AudiobookBook(Table):
    uploaded_by = Text()
    book_title = Text()
    book_author = Text()
    chapter_count = Integer()
    upload_date = Timestamptz()
    custom_book_title = Text()
    custom_book_author = Text()
    # Soft delete flag
    deleted = Boolean()


class AudiobookChapter(Table):
    book = ForeignKey(references=AudiobookBook)
    queued = Timestamptz()
    started_converting = Timestamptz()
    chapter_title = Text()
    chapter_number = Integer()
    word_count = Integer()
    sentence_count = Integer()
    content = Text()
    minio_object_name = Text()
    audi_settings = JSON()
