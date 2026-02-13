from pathlib import Path

import rio

from minio_helper import (
    MINIO_AUDIOBOOK_BUCKET,
    get_s3_client,
    object_create_presigned_url,
)
from models.audiobook import AudiobookBook, AudiobookChapter
from rio_app.components.audiobook.book_page.component_audiobook_settings import AudiobookSettingsComponent
from rio_app.components.audiobook.book_page.component_book import BookComponent
from rio_app.components.audiobook.book_page.component_chapter import AudiobookChapterComponent
from rio_app.components.audiobook.generate_tts import get_supported_voices
from rio_app.components.audiobook.models import (
    AudiobookChapterQueryResult,
    AudioSettings,
    delete_audio_for_chapters,
)
from rio_app.components.login.cookies import LoggedInUser, logged_in_guard

queries_directory = Path(__file__).parents[3] / "queries"
query_get_chapters = (queries_directory / "audiobook_get_chapters.sql").read_text()


@rio.page(
    url_segment="book/{book_id}",
    guard=logged_in_guard,
)
class AudiobookBookPage(rio.Component):
    book_id: int
    is_loading: bool = True
    user_has_access: bool = False

    book_data: AudiobookBook | None = None
    chapters_data: list[AudiobookChapterQueryResult] = []
    available_voices: list[str] = []

    @rio.event.on_mount
    async def on_mount(self):
        logged_in_user = self.session[LoggedInUser]
        # Check if user owns this book
        book = await AudiobookBook.objects().get(
            # pyrefly: ignore
            (AudiobookBook.id == self.book_id) & (AudiobookBook.uploaded_by == logged_in_user.db_name)
        )
        if book is None:
            self.is_loading = False
            return
        await self.session.set_title(
            f"Book: {book.custom_book_author or book.book_author} - {book.custom_book_title or book.book_title}"
        )
        self.user_has_access = True
        self.book_data = book

        # Grab chapter info
        chapters_info_response: list[dict] = await AudiobookChapter.raw(
            query_get_chapters, self.book_id, [i + 1 for i in range(self.book_data.chapter_count)]
        )
        self.chapters_data = [AudiobookChapterQueryResult(**row) for row in chapters_info_response]

        # Handle auto deletion from minio - minio url might be invalid for audio because minio autodeletes files
        # after some time, set to None then
        chapters_with_expired_object_name = await self.create_presigned_urls(self.chapters_data)
        await delete_audio_for_chapters(chapters_with_expired_object_name)

        # Grab available voices
        self.available_voices = await get_supported_voices()

        # Grab user audio settings from localstorage
        audio_settings = self.session[AudioSettings]
        # Set voice to first available
        if 0 < len(self.available_voices) and audio_settings.voice not in self.available_voices:
            audio_settings.voice = self.available_voices[0]
            self.session.attach(audio_settings)

        self.is_loading = False

    @rio.event.periodic(10)
    async def periodic(self):
        # Update queued chapters
        if self.is_loading or self.book_data is None:
            return
        chapter_numbers_needing_refresh: list[int] = [
            c.chapter_number for c in self.chapters_data if c.number_in_queue is not None or c.is_converting is True
        ]
        if len(chapter_numbers_needing_refresh) == 0:
            return
        await self.refresh_chapters(chapter_numbers_needing_refresh)

    async def refresh_chapters(self, chapter_numbers_needing_refresh: list[int]):
        chapters_info_response: list[dict] = await AudiobookChapter.raw(
            query_get_chapters, self.book_id, chapter_numbers_needing_refresh
        )
        chapters_data = [AudiobookChapterQueryResult(**row) for row in chapters_info_response]
        for chapter in chapters_data:
            self.chapters_data[chapter.chapter_number - 1] = chapter
        await self.create_presigned_urls(self.chapters_data)
        self.force_refresh()

    async def create_presigned_urls(self, chapters: list[AudiobookChapterQueryResult]):
        chapters_with_expired_object_name = list[AudiobookChapterQueryResult]()
        async with get_s3_client() as s3:
            # TODO Get presigned urls for all of them at the same time
            for chapter in chapters:
                if chapter.minio_presigned_url != "":
                    continue
                if chapter.minio_object_name is None:
                    continue
                url = await object_create_presigned_url(
                    s3,
                    MINIO_AUDIOBOOK_BUCKET,
                    chapter.minio_object_name,
                    file_name=f"chapter_{chapter.chapter_number}.mp3",
                )
                if url is None:
                    chapter.minio_object_name = None
                    chapters_with_expired_object_name.append(chapter)
                    continue
                chapter.minio_presigned_url = url
        return chapters_with_expired_object_name

    def build(self) -> rio.Component:
        if self.is_loading:
            return rio.ProgressCircle(align_x=0.5)
        if not self.user_has_access:
            return rio.Text(
                text="You don't have access to this book!",
                # pyrefly: ignore
                align_x=0.5,
                # pyrefly: ignore
                align_y=0.5,
            )

        # Render chapters
        my_grid: list[list[rio.Component]] = []
        for chapter in self.chapters_data:
            my_grid.append(
                [
                    rio.Text(
                        f"'{chapter.chapter_title}' with {chapter.sentence_count} sentences",
                        grow_x=True,  # pyrefly: ignore
                        overflow="wrap",
                    ),
                    AudiobookChapterComponent(chapter),
                ]
            )

        assert self.book_data is not None
        return rio.Column(
            BookComponent(self.book_data),
            AudiobookSettingsComponent(self.chapters_data, self.available_voices, self.book_id, self.refresh_chapters),
            rio.Rectangle(
                content=rio.Column(
                    rio.Text(
                        "Table of Contents",
                        style="heading2",
                        align_x=0.5,  # pyrefly: ignore
                    ),
                    rio.Grid(
                        *my_grid,
                        min_width=50,
                        margin=1,
                        row_spacing=0.5,
                    ),
                ),
                stroke_width=0.2,
                stroke_color=rio.Color.PURPLE,
                corner_radius=2,
            ),
            align_x=0.5,
            align_y=0.5,
            spacing=1,
        )
