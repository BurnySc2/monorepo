import asyncio
import io
from contextlib import contextmanager
from functools import partial

import arrow
import rio
from rio_app.components.audiobook.epub_reader import EpubChapter, EpubMetadata, extract_chapters, extract_metadata
from rio_app.components.login.cookies import LoggedInUser

from minio_helper import GARAGE_AUDIOBOOK_BUCKET, get_s3_client, object_delete
from models.audiobook import AudiobookBook, AudiobookChapter
from piccolo_conf import DB


class AudiobookBooksOverview(rio.Component):
    uploaded_books: list[AudiobookBook]

    def on_book_click(self, book_id: int):
        self.session.navigate_to(f"/audiobook/book/{book_id}")

    async def on_delete_book(self, id_in_list: int, book_id: int):
        async with DB.transaction():
            # Delete audio from minio
            chapters = await AudiobookChapter.objects().where(AudiobookChapter.book == book_id)
            async with get_s3_client() as s3:
                for chapter in chapters:
                    if chapter.minio_object_name is None:
                        continue
                    await object_delete(s3, GARAGE_AUDIOBOOK_BUCKET, chapter.minio_object_name)
            # Delete chapters from db
            await AudiobookChapter.delete().where(AudiobookChapter.book == book_id)
            # Delete book from db
            await AudiobookBook.delete().where(
                # pyrefly: ignore
                AudiobookBook.id == book_id
            )
        # Update UI
        self.uploaded_books.pop(id_in_list)
        self.force_refresh()

    def build(self):
        header_row = [
            rio.Text("Upload date", font_weight="bold"),
            rio.Text("Book title", font_weight="bold"),
            rio.Text("Book author", font_weight="bold"),
            rio.Text("Chapters", font_weight="bold"),
            rio.Text("Remove Book", font_weight="bold"),
        ]
        rows = [
            [
                rio.Text(arrow.get(b.upload_date).format("YYYY-MM-DD")),
                rio.Button(
                    b.custom_book_title or b.book_title,
                    style="plain-text",
                    shape="rounded",
                    # pyrefly: ignore
                    align_x=0,
                    # pyrefly: ignore
                    on_press=partial(self.on_book_click, b.id),
                ),
                rio.Button(
                    b.custom_book_author or b.book_author,
                    style="plain-text",
                    shape="rounded",
                    # pyrefly: ignore
                    align_x=0,
                    # pyrefly: ignore
                    on_press=partial(self.on_book_click, b.id),
                ),
                rio.Text(str(b.chapter_count)),
                rio.IconButton(
                    "material/delete_forever",
                    # pyrefly: ignore
                    on_press=partial(self.on_delete_book, i, b.id),
                    color=rio.Color.from_oklab(0.25, 0.5, 0.2),
                ),
            ]
            for i, b in enumerate(self.uploaded_books)
        ]
        return rio.Grid(header_row, *rows, column_spacing=2)


@rio.page(
    name="Audiobook List",
    url_segment="",
)
class AudiobookRootPage(rio.Component):
    is_loading: bool = True
    is_logged_in: bool = False
    book_processing: bool = False

    uploaded_books: list[AudiobookBook] = []

    @rio.event.on_mount
    async def on_mount(self):
        @contextmanager
        def set_loading_to_false_afterwards():
            try:
                yield
            finally:
                self.is_loading = False

        with set_loading_to_false_afterwards():
            logged_in_user = self.session[LoggedInUser]
            self.is_logged_in = True
            books = (
                await AudiobookBook.objects()
                .where(AudiobookBook.uploaded_by == logged_in_user.db_name)
                .order_by(AudiobookBook.upload_date, ascending=False)
            )
            if len(books) == 0:
                return
            self.uploaded_books = books

    async def on_file_drop(self, event: rio.FilePickEvent):
        # TODO File size limit 100mb
        self.book_processing = True

        epub_data = io.BytesIO(await event.file.read_bytes())
        metadata: EpubMetadata = await asyncio.to_thread(extract_metadata, epub_data)

        logged_in_user = self.session[LoggedInUser]
        # Book exists?
        book = (
            # pyrefly: ignore
            await AudiobookBook.objects()
            # pyrefly: ignore
            .where(
                (AudiobookBook.uploaded_by == logged_in_user.db_name)
                & (AudiobookBook.book_title == metadata.title)
                & (AudiobookBook.book_author == metadata.author)
            )
            .first()
        )
        if book is not None:
            # Already present
            return self.session.navigate_to(
                f"/audiobook/book/{book.id}",  # pyrefly: ignore
            )

        # TODO If user uploaded X books in the last Y days, return error that too many books were uploaded

        chapters: list[EpubChapter] = await asyncio.to_thread(extract_chapters, epub_data)

        # Insert book
        async with DB.transaction():
            book = await AudiobookBook(
                uploaded_by=logged_in_user.db_name,
                book_title=metadata.title,
                book_author=metadata.author,
                chapter_count=len(chapters),
            ).save()
            book = book[0]
            # Insert chapters
            if 0 < len(chapters):
                await AudiobookChapter.insert(
                    *[
                        AudiobookChapter(
                            book=book["id"],
                            chapter_title=chapter.chapter_title,
                            chapter_number=chapter.chapter_number,
                            word_count=chapter.word_count,
                            sentence_count=chapter.sentence_count,
                            content=chapter.combined_text,
                        )
                        for chapter in chapters
                    ]
                )
        self.book_processing = False
        return self.session.navigate_to(
            f"/audiobook/book/{book['id']}",
        )

    def build(self):
        if not self.is_loading and not self.is_logged_in:
            return rio.Text(
                "Log in before you can upload books.",
                # pyrefly: ignore
                align_x=0.5,
            )
        if self.book_processing:
            return rio.ProgressCircle(align_x=0.5)
        col = rio.Column(
            # pyrefly: ignore
            rio.Text("Audiobooks", style="heading1", font_weight="bold", align_x=0.5),
            rio.FilePickerArea(
                content="Drop your .epub book here to upload", on_pick_file=self.on_file_drop, file_types=["epub"]
            ),
            align_x=0.5,
            align_y=0.5,
            spacing=2,
        )
        if self.is_loading:
            col.children.append(rio.ProgressCircle())
        elif len(self.uploaded_books) == 0:
            col.children.append(rio.Text("Your uploaded books will appear here."))
        else:
            col.children.append(AudiobookBooksOverview(self.bind().uploaded_books))
        return col
