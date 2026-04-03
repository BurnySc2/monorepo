import arrow
import rio

from minio_helper import (
    GARAGE_AUDIOBOOK_BUCKET,
    get_s3_client,
    object_create_presigned_url,
)
from models.audiobook import AudiobookBook, AudiobookChapter
from piccolo_conf import DB
from rio_app.components.audiobook.models import (
    AudiobookChapterQueryResult,
    AudioSettings,
    AudioSettingsBaseModel,
    delete_audio_for_chapters,
    get_book_minio_zip_name,
    normalize_title,
    upload_multipart_book,
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
                    GARAGE_AUDIOBOOK_BUCKET,
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
        await delete_audio_for_chapters(self.chapters)
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

    def on_rate_change(self, event: rio.NumberInputChangeEvent):
        audio_settings = self.session[AudioSettings]
        audio_settings.rate = int(event.value)
        self.session.attach(audio_settings)

    def on_volume_change(self, event: rio.NumberInputChangeEvent):
        audio_settings = self.session[AudioSettings]
        audio_settings.volume = int(event.value)
        self.session.attach(audio_settings)

    def on_pitch_change(self, event: rio.NumberInputChangeEvent):
        audio_settings = self.session[AudioSettings]
        audio_settings.pitch = int(event.value)
        self.session.attach(audio_settings)

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
                    [
                        # pyrefly: ignore
                        rio.Text("Rate", align_x=1),
                        rio.NumberInput(value=audio_settings.rate, decimals=0, on_change=self.on_rate_change),
                    ],
                    [
                        # pyrefly: ignore
                        rio.Text("Volume", align_x=1),
                        rio.NumberInput(value=audio_settings.volume, decimals=0, on_change=self.on_volume_change),
                    ],
                    [
                        # pyrefly: ignore
                        rio.Text("Pitch", align_x=1),
                        rio.NumberInput(value=audio_settings.pitch, decimals=0, on_change=self.on_pitch_change),
                    ],
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
