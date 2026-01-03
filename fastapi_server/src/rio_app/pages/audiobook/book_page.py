from pathlib import Path
from stat import S_IFREG

import arrow
import rio
from pydantic import BaseModel
from stream_zip import NO_COMPRESSION_64, async_stream_zip

from minio_helper import (
    AUDIOBOOK_BUCKET,
    get_s3_client,
    object_create_presigned_url,
    object_delete,
    object_download,
    object_upload_async_iterable,
)
from models.audiobook import AudiobookBook, AudiobookChapter
from piccolo_conf import DB
from rio_app.components.audiobook.generate_tts import get_supported_voices
from rio_app.components.audiobook.models import (
    AudioSettings,
    AudioSettingsBaseModel,
    normalize_filename,
    normalize_title,
)
from rio_app.components.login.cookies import LoggedInUser, logged_in_guard

queries_directory = Path(__file__).parents[3] / "queries"
query_get_chapters = (queries_directory / "audiobook_get_chapters.sql").read_text()


class AudiobookChapterQueryResult(BaseModel):
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


def get_book_minio_zip_name(book_id: int) -> str:
    return f"book_{book_id}.zip"


async def delete_audio_for_chapters(book_id: int, chapters: list[AudiobookChapterQueryResult]) -> None:
    # Delete audiobook zip from minio if exists
    # Delete audio for chapter from minio if exists
    # Set chapters to not have audio for ids
    chapter_ids: list[int] = [chapter.id for chapter in chapters]
    async with DB.transaction():
        async with get_s3_client() as s3:
            # Delete book zip - doesn't matter as we re-generate the zip for each download
            # await object_delete(s3, AUDIOBOOK_BUCKET, get_book_minio_zip_name(book_id))

            # Delete audio for chapters
            for chapter in chapters:
                if chapter.minio_object_name is None:
                    continue
                await object_delete(s3, AUDIOBOOK_BUCKET, chapter.minio_object_name)

        # Set chapters in db to unqueued
        await AudiobookChapter.update(
            {
                AudiobookChapter.queued: None,
                AudiobookChapter.started_converting: None,
                AudiobookChapter.minio_object_name: None,
                AudiobookChapter.audio_settings: None,
            }
        ).where(
            # pyrefly: ignore
            AudiobookChapter.id.is_in(chapter_ids)
        )


async def upload_multipart_book(book: AudiobookBook, chapters: list[AudiobookChapterQueryResult]):
    assert book is not None
    normalized_author = f"{normalize_title(book.custom_book_author or book.book_author)}"[:50].strip()
    normalized_book_title = f"{normalize_title(book.custom_book_title or book.book_title)}"[:150].strip()

    async with get_s3_client() as s3:

        async def chapter_audio_chunks():
            for chapter in chapters:
                assert chapter.minio_object_name is not None
                obj = await object_download(s3, AUDIOBOOK_BUCKET, chapter.minio_object_name)
                assert obj is not None

                async def yield_data():
                    assert obj is not None
                    yield obj

                normalized_chapter_name = normalize_filename(chapter.chapter_title)[:200].strip()
                audio_file_name = f"{normalized_author}/{normalized_book_title}/{chapter.chapter_number:04d}_{normalized_chapter_name}.mp3"  # noqa: E501
                yield (
                    audio_file_name,
                    arrow.utcnow().naive,
                    S_IFREG | 0o600,
                    # ZIP_64,  # Use compression to save about 4%
                    NO_COMPRESSION_64,  # Don't use compression
                    yield_data(),
                )

        await object_upload_async_iterable(
            s3,
            AUDIOBOOK_BUCKET,
            # pyrefly: ignore
            get_book_minio_zip_name(book.id),
            async_stream_zip(chapter_audio_chunks()),
        )


class BookComponent(rio.Component):
    book: AudiobookBook

    custom_book_title: str = ""
    custom_book_author: str = ""

    edit_title: bool = False
    edit_author: bool = False

    @rio.event.on_mount
    def on_moun(self):
        self.custom_book_title = self.book.custom_book_title or self.book.book_title
        self.custom_book_author = self.book.custom_book_author or self.book.book_author

    async def on_custom_title_confirm(self, value: rio.TextInputConfirmEvent):
        await self.on_edit_title_button()

    async def on_custom_author_confirm(self, value: rio.TextInputConfirmEvent):
        await self.on_edit_author_button()

    async def on_edit_title_button(self):
        self.edit_title = not self.edit_title
        if self.edit_title is False:
            # Save custom title in db to fetch later when downloading book
            self.book.custom_book_title = self.custom_book_title
            await AudiobookBook.update(
                {
                    AudiobookBook.custom_book_title: self.custom_book_title,
                }
                # pyrefly: ignore
            ).where(AudiobookBook.id == self.book.id)
        if self.custom_book_title == "":
            self.custom_book_title = self.book.book_title

    async def on_edit_author_button(self):
        self.edit_author = not self.edit_author
        if self.edit_author is False:
            # Save custom author in db to fetch later when downloading book
            self.book.custom_book_author = self.custom_book_author
            await AudiobookBook.update(
                {
                    AudiobookBook.custom_book_author: self.custom_book_author,
                }
                # pyrefly: ignore
            ).where(AudiobookBook.id == self.book.id)
        if self.custom_book_author == "":
            self.custom_book_author = self.book.book_author

    def build(self) -> rio.Component:
        row_book_title = rio.Row(spacing=1, grow_x=True)
        if self.edit_title:
            row_book_title.children.append(
                rio.TextInput(
                    # pyrefly: ignore
                    self.bind().custom_book_title,
                    # pyrefly: ignore
                    on_confirm=self.on_custom_title_confirm,
                    text_style=rio.TextStyle(font_size=2),
                    label="Book title",
                    grow_x=True,  # pyrefly: ignore
                )
            )
        else:
            row_book_title.children.append(
                rio.Text(
                    f"{self.book.custom_book_title or self.book.book_title}",
                    style="heading1",
                    align_x=1,  # pyrefly: ignore
                )
            )
        row_book_title.children.append(
            rio.IconButton("material/edit_square", align_x=1, style="colored-text", on_press=self.on_edit_title_button)
        )

        row_book_author = rio.Row(spacing=1, grow_x=True)
        if self.edit_author:
            row_book_author.children.append(
                rio.TextInput(
                    # pyrefly: ignore
                    self.bind().custom_book_author,
                    on_confirm=self.on_custom_author_confirm,
                    text_style=rio.TextStyle(font_size=2),
                    label="Author name",
                    grow_x=True,  # pyrefly: ignore
                )
            )
        else:
            row_book_author.children.append(
                rio.Text(
                    f"{self.book.custom_book_author or self.book.book_author}",
                    style="heading1",
                    align_x=1,  # pyrefly: ignore
                )
            )
        row_book_author.children.append(
            rio.IconButton("material/edit_square", align_x=1, style="colored-text", on_press=self.on_edit_author_button)
        )

        return rio.Column(row_book_title, row_book_author)


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
                    AudiobookChapter.queued: arrow.utcnow().naive,
                    AudiobookChapter.audio_settings: AudioSettingsBaseModel.from_dataclass(
                        audio_settings
                    ).model_dump_json(),
                }
            )
            .where(
                (AudiobookChapter.book == self.book_id)
                & (AudiobookChapter.queued == None)  # noqa: E711
                & (AudiobookChapter.minio_object_name == None)  # noqa: E711
            )
            .returning(AudiobookChapter.chapter_number)
        )
        await self.call_event_handler(self.refresh_chapters, [c["chapter_number"] for c in updated_chapters])

    async def prepare_book_download_and_redirect(self):
        assert all(chapter.has_audio for chapter in self.chapters), (
            "All chapters need to have audio generated for this to work"
        )
        book = await AudiobookBook.objects().get(AudiobookBook.id == self.book_id)  # pyrefly: ignore

        # If object exists, redirect
        async def download_book_object():
            assert book is not None
            async with get_s3_client() as s3:
                normalized_author = f"{normalize_title(book.custom_book_author or book.book_author)}"[:50].strip()
                normalized_book_title = f"{normalize_title(book.custom_book_title or book.book_title)}"[:150].strip()
                url = await object_create_presigned_url(
                    s3,
                    AUDIOBOOK_BUCKET,
                    get_book_minio_zip_name(self.book_id),
                    f"{normalized_author} - {normalized_book_title}.zip",
                    verify_object_exists=True,
                )
                if url is not None:
                    self.session.navigate_to(url)
                    return True
            return False

        # Book title or author may have changed, always re-generate .zip
        # already_exists = await download_book_object()
        # if already_exists:
        #     return

        assert book is not None
        await upload_multipart_book(book, self.chapters)
        await download_book_object()

    async def delete_all_audio_for_book(self):
        await delete_audio_for_chapters(self.book_id, self.chapters)
        await self.call_event_handler(self.refresh_chapters, [c.chapter_number for c in self.chapters])

    async def delete_book(self):
        async with DB.transaction():
            # pyrefly: ignore
            await AudiobookBook.delete().where(AudiobookBook.id == self.book_id)
            # pyrefly: ignore
            await AudiobookChapter.delete().where(AudiobookChapter.book == self.book_id)
        await self.call_event_handler(self.refresh_chapters, [c.chapter_number for c in self.chapters])

    @property
    def is_button_generate_audio_enabled(self) -> bool:
        # TODO Needs to react on chapter deletions and new queues, return True for now
        return True
        # def can_generate_audio(chapter: AudiobookChapterQueryResult) -> bool:
        #     if chapter.has_audio:
        #         return False
        #     if chapter.number_in_queue is not None:
        #         return False
        #     return not chapter.is_converting

        # return any(can_generate_audio(c) for c in self.chapters)

    @property
    def is_button_download_enabled(self) -> bool:
        # TODO Same as above
        return True
        # return all(c.has_audio for c in self.chapters)

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
                        on_press=self.prepare_book_download_and_redirect,
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
                        on_press=self.delete_book,
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


class AudiobookChapterComponent(rio.Component):
    chapter: AudiobookChapterQueryResult

    async def chapter_queue(self):
        # Change chapter to be queued
        audio_settings = self.session[AudioSettings]
        await AudiobookChapter.update(
            {
                AudiobookChapter.queued: arrow.utcnow().naive,
                AudiobookChapter.audio_settings: AudioSettingsBaseModel.from_dataclass(
                    audio_settings
                ).model_dump_json(),
            }
        ).where(
            AudiobookChapter.id == self.chapter.id  # pyrefly: ignore
        )
        self.chapter.number_in_queue = -1
        self.force_refresh()

    async def chapter_download(self):
        # Create presigned url and redirect user to trigger download
        if self.chapter.minio_object_name is None:
            return
        async with get_s3_client() as s3:
            obj = await object_create_presigned_url(
                s3,
                AUDIOBOOK_BUCKET,
                self.chapter.minio_object_name,
                f"{self.chapter.chapter_number:04d}_{normalize_filename(self.chapter.chapter_title)}.mp3",
            )
            if obj is not None:
                self.session.navigate_to(obj)
                # self.session.open_url_in_browser(obj)

    async def chapter_audio_delete(self):
        # Change chapter entry in db to no longer have audio
        await delete_audio_for_chapters(self.chapter.book_id, [self.chapter])
        self.chapter.has_audio = False
        self.chapter.number_in_queue = None
        self.chapter.is_converting = False
        self.force_refresh()

    def build(self):
        row = rio.Row(
            spacing=0.5,
        )
        if self.chapter.has_audio:
            row.children.extend(
                [
                    rio.Webview(
                        f"""
<audio controls preload="metadata" id="audio">
    <source src="{self.chapter.minio_presigned_url}" type="audio/mpeg">
    Your browser does not support the audio element.
</audio>
""".strip()
                    ),
                    # rio.MediaPlayer(rio.URL(self.chapter.minio_presigned_url), media_type="audio/mp3"),
                    rio.IconButton(
                        "material/download",
                        on_press=self.chapter_download,
                        align_x=1,
                    ),
                    rio.IconButton(
                        "material/delete",
                        on_press=self.chapter_audio_delete,
                        align_x=1,
                        color=rio.Color.from_oklab(0.25, 0.5, 0.2),
                    ),
                ]
            )
        elif self.chapter.number_in_queue is not None:
            text = "Queued ..."
            if 0 < self.chapter.number_in_queue:
                text = f"Queued ({self.chapter.number_in_queue})"
            row.children.extend(
                [
                    rio.ProgressCircle(align_x=0),
                    rio.Text(
                        text,
                        align_x=0,  # pyrefly: ignore
                        grow_x=True,  # pyrefly: ignore
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
            row.children.extend(
                [
                    rio.ProgressCircle(align_x=0),
                    rio.Text(
                        "Generating audio ...",
                        align_x=0,  # pyrefly: ignore
                        grow_x=True,  # pyrefly: ignore
                    ),
                ]
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

        await self.create_presigned_urls(self.chapters_data)

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
        async with get_s3_client() as s3:
            # TODO Get presigned urls for all of them at the same time
            for chapter in chapters:
                if chapter.minio_presigned_url != "":
                    continue
                if chapter.minio_object_name is None:
                    continue
                url = await object_create_presigned_url(
                    s3, AUDIOBOOK_BUCKET, chapter.minio_object_name, file_name=f"chapter_{chapter.chapter_number}.mp3"
                )
                if url is None:
                    continue
                chapter.minio_presigned_url = url

    def build(self) -> rio.Component:
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
