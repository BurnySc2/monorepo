from pathlib import Path

import arrow
import rio
from pydantic import BaseModel

from models.audiobook import AudiobookBook, AudiobookChapter
from rio_app.components.audiobook.generate_tts import get_supported_voices
from rio_app.components.audiobook.models import AudioSettings
from rio_app.components.login.cookies import LoggedInUser, logged_in_guard

queries_directory = Path(__file__).parents[3] / "queries"
query_get_chapters = (queries_directory / "audiobook_get_chapters.sql").read_text()


class AudiobookChapterQueryResult(BaseModel):
    # Class used in other contexts
    id: int
    book_id: int
    number_in_queue: int | None  # 'None' if converting or not queued
    is_converting: bool
    has_audio: bool
    chapter_title: str
    chapter_number: int
    # word_count: int
    sentence_count: int
    minio_object_name: str | None
    # Filled after query
    minio_presigned_url: str = ""


class BookComponent(rio.Component):
    book: AudiobookBook

    def build(self):
        # TODO After clicking on edit, allow user to change title and author name
        return rio.Column(
            rio.Row(
                # pyrefly: ignore
                rio.Text(f"{self.book.book_title}", style="heading1", align_x=1),
                rio.IconButton("material/edit_square", align_x=0, style="colored-text"),
                spacing=1,
            ),
            rio.Row(
                # pyrefly: ignore
                rio.Text(f"{self.book.book_author}", style="heading1", align_x=1),
                rio.IconButton("material/edit_square", align_x=0, style="colored-text"),
                spacing=1,
            ),
        )


class AudiobookSettingsComponent(rio.Component):
    chapters: list[AudiobookChapterQueryResult]
    available_voices: list[str]
    book_id: int

    refresh_chapters: rio.EventHandler[list[int]] = None

    async def queue_audio_for_all_chapters(self):
        audio_settings = self.session[AudioSettings]
        updated_chapters = (
            await AudiobookChapter.update(
                {
                    "queued": arrow.utcnow().naive,
                    "audio_settings": audio_settings.__dict__,
                }
            )
            .where(
                (AudiobookChapter.book == self.book_id)
                & (AudiobookChapter.queued == None)  # pyrefly: ignore # noqa: E711
            )
            .returning(AudiobookChapter.chapter_number)
        )
        await self.call_event_handler(self.refresh_chapters, [c["chapter_number"] for c in updated_chapters])

    async def delete_all_audio_for_book(self):
        await AudiobookChapter.update(
            {
                "queued": None,
                "minio_object_name": None,
                "audio_settings": None,
            }
        ).where(
            AudiobookChapter.book == self.book_id  # pyrefly: ignore
        )
        await self.call_event_handler(self.refresh_chapters, [c.chapter_number for c in self.chapters])

    # TODO Download book handler

    # TODO Delete book handler

    @property
    def is_button_generate_audio_enabled(self) -> bool:
        def can_generate_audio(chapter: AudiobookChapterQueryResult) -> bool:
            if chapter.has_audio:
                return False
            if chapter.number_in_queue is not None:
                return False
            return not chapter.is_converting

        return any(can_generate_audio(c) for c in self.chapters)

    @property
    def is_button_download_enabled(self) -> bool:
        return all(c.has_audio for c in self.chapters)

    def on_voice_change(self, event: rio.DropdownChangeEvent):
        audio_settings = self.session[AudioSettings]
        audio_settings.voice = event.value
        self.session.attach(audio_settings)

    # TODO Other change handlers

    def build(self):
        audio_settings = self.session[AudioSettings]

        return rio.Rectangle(
            content=rio.Column(
                # pyrefly: ignore
                rio.Text("Settings", style="heading2", align_x=0.5),
                rio.Grid(
                    [
                        # pyrefly: ignore
                        rio.Text("Voice", align_x=1),
                        rio.Dropdown(
                            self.available_voices, on_change=self.on_voice_change, selected_value=audio_settings.voice
                        ),
                    ],
                    # pyrefly: ignore
                    [rio.Text("Rate", align_x=1), rio.NumberInput(0, decimals=0)],
                    # pyrefly: ignore
                    [rio.Text("Volume", align_x=1), rio.NumberInput(0, decimals=0)],
                    # pyrefly: ignore
                    [rio.Text("Pitch", align_x=1), rio.NumberInput(0, decimals=0)],
                    column_spacing=1,
                ),
                rio.Row(
                    rio.Button(
                        "Generate audio for all chapters",
                        color="success",
                        is_sensitive=self.is_button_generate_audio_enabled,
                        on_press=self.queue_audio_for_all_chapters,
                        grow_x=True,  # pyrefly: ignore
                    ),
                    rio.Button(
                        "Download book",
                        color="primary",
                        is_sensitive=self.is_button_download_enabled,
                        grow_x=True,  # pyrefly: ignore
                    ),
                    rio.Button(
                        "Delete all audio",
                        color=rio.Color.from_oklab(0.25, 0.5, 0.2),
                        on_press=self.delete_all_audio_for_book,
                        grow_x=True,  # pyrefly: ignore
                    ),
                    rio.Button(
                        "Delete book",
                        color=rio.Color.from_oklab(0.25, 0.5, 0.2),
                        grow_x=True,  # pyrefly: ignore
                    ),
                    spacing=1,
                ),
                spacing=1,
                margin=1,
            ),
            stroke_width=0.2,
            stroke_color=rio.Color.PURPLE,
            corner_radius=2,
        )


TEST_HTML = """
<audio controls="" preload="metadata" id="audio">
    <source src="https://minio.burnysc2.xyz/staging-audiobooks/1379_audio.mp3?X-Amz-Algorithm=AWS4-HMAC-SHA256&amp;X-Amz-Credential=s40LqDjsa7CtorQDL62F%2F20260101%2Fus-east-1%2Fs3%2Faws4_request&amp;X-Amz-Date=20260101T131356Z&amp;X-Amz-Expires=86400&amp;X-Amz-SignedHeaders=host&amp;X-Amz-Signature=cbf6f99379a393addf7bf5059ae0a051b92d1e2bd1445bcb0d88d2288bcfa7d0" type="audio/mpeg">
    Your browser does not support the audio element.
</audio>
"""


class AudiobookChapterComponent(rio.Component):
    chapter: AudiobookChapterQueryResult

    # TODO Download audio event handler

    async def chapter_queue(self):
        # Change chapter to be queued
        audio_settings = self.session[AudioSettings]
        await AudiobookChapter.update(
            {
                "queued": arrow.utcnow().naive,
                "audio_settings": audio_settings.__dict__,
            }
        ).where(
            AudiobookChapter.id == self.chapter.id  # pyrefly: ignore
        )
        self.chapter.number_in_queue = -1
        self.force_refresh()

    async def chapter_download(self):
        # Create presigned url and redirect user
        pass

    async def chapter_audio_delete(self):
        # Change chapter entry in db to no longer have audio
        await AudiobookChapter.update(
            {
                "queued": None,
                "minio_object_name": None,
                "audio_settings": None,
            }
        ).where(
            # pyrefly: ignore
            AudiobookChapter.id == self.chapter.id
        )
        self.chapter.has_audio = False
        self.chapter.number_in_queue = None
        self.chapter.is_converting = False
        self.force_refresh()
        # TODO Delete minio audio file

    def build(self):
        row = rio.Row(
            spacing=0.5,
        )
        if self.chapter.has_audio:
            row.children.extend(
                [
                    rio.Webview(
                        self.chapter.minio_presigned_url,
                        align_x=1,  # pyrefly: ignore
                    ),
                    rio.IconButton(
                        "material/download",
                        align_x=1,
                    ),
                    rio.IconButton(
                        "material/delete",
                        align_x=1,
                        color=rio.Color.from_oklab(0.25, 0.5, 0.2),
                        on_press=self.chapter_audio_delete,
                    ),
                ]
            )
        elif self.chapter.number_in_queue is not None:
            text = "Queued ..."
            if 0 < self.chapter.number_in_queue:
                text = f"Queued ({self.chapter.number_in_queue})"
            row.children.extend(
                [
                    rio.ProgressCircle(align_x=1),
                    rio.Text(
                        text,
                        align_x=1,  # pyrefly: ignore
                    ),
                    rio.IconButton(
                        "material/delete",
                        align_x=1,
                        color=rio.Color.from_oklab(0.25, 0.5, 0.2),
                        on_press=self.chapter_audio_delete,
                    ),
                ]
            )
        elif self.chapter.is_converting:
            row.children.append(
                rio.Text(
                    "Generating audio...)",
                    align_x=1,  # pyrefly: ignore
                )
            )
            row.children.append(
                rio.IconButton(
                    "material/delete",
                    align_x=1,
                    color=rio.Color.from_oklab(0.25, 0.5, 0.2),
                    on_press=self.chapter_audio_delete,
                ),
            )
        else:
            row.children.append(rio.Button("Generate audio", color="success", on_press=self.chapter_queue))
        return row


@rio.page(
    name="TODO according to book",
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

    async def refresh_chapters(self, chapter_numbers_needing_refresh: list[int]):
        chapters_info_response: list[dict] = await AudiobookChapter.raw(
            query_get_chapters, self.book_id, chapter_numbers_needing_refresh
        )
        chapters_data = [AudiobookChapterQueryResult(**row) for row in chapters_info_response]
        for chapter in chapters_data:
            self.chapters_data[chapter.chapter_number - 1] = chapter
        self.force_refresh()

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
        self.user_has_access = True
        self.book_data = book

        # Grab chapter info
        chapters_info_response: list[dict] = await AudiobookChapter.raw(
            query_get_chapters, self.book_id, [i + 1 for i in range(self.book_data.chapter_count)]
        )
        self.chapters_data = [AudiobookChapterQueryResult(**row) for row in chapters_info_response]

        # Grab available voices
        self.available_voices = await get_supported_voices()

        # Grab user audio settings from localstorage
        audio_settings = self.session[AudioSettings]
        # Set voice to first available
        if 0 < len(self.available_voices) and audio_settings.voice not in self.available_voices:
            audio_settings.voice = self.available_voices[0]
            self.session.attach(audio_settings)

        self.is_loading = False

    def build(self):
        if self.is_loading:
            return rio.ProgressCircle(align_x=0.5)
        if not self.user_has_access:
            return rio.Text("You don't have access to this book!")

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
