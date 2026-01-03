import asyncio
import io

import rio

from models.audiobook import AudiobookBook, AudiobookChapter
from piccolo_conf import DB
from rio_app.components.audiobook.epub_reader import EpubChapter, EpubMetadata, extract_chapters, extract_metadata
from rio_app.components.login.cookies import LoggedInUser

data = {
    "Name": ["Alice", "Bob", "Charlie"],
    "Age": [25, 30, 35],
    "City": ["New York", "San Francisco", "Los Angeles"],
}


@rio.page(
    name="Audiobook List",
    url_segment="",
)
class AudiobookRootPage(rio.Component):
    # TODO List already uploaded books
    # TODO Clicking on book redirects to book page
    # TODO Allow user to delete book from the list
    # TODO Add button to delete all books

    book_processing: bool = False

    async def on_file_drop(self, event: rio.FilePickEvent):
        # TODO File size limit 100mb
        self.book_processing = True

        epub_data = io.BytesIO(await event.file.read_bytes())
        metadata: EpubMetadata = await asyncio.to_thread(extract_metadata, epub_data)

        # Book exists?
        logged_in_user = self.session[LoggedInUser]
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
        if self.book_processing:
            return rio.ProgressCircle(align_x=0.5)
        return rio.Column(
            # pyrefly: ignore
            rio.Text("Audiobooks", style="heading1", font_weight="bold", align_x=0.5),
            rio.FilePickerArea(on_pick_file=self.on_file_drop),
            rio.Table(data=data, show_row_numbers=False),
            align_x=0.5,
            align_y=0.5,
            spacing=1,
        )
