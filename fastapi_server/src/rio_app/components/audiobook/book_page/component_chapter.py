import arrow
import rio

from minio_helper import (
    AUDIOBOOK_BUCKET,
    get_s3_client,
    object_create_presigned_url,
)
from models.audiobook import AudiobookChapter
from rio_app.components.audiobook.models import (
    AudiobookChapterQueryResult,
    AudioSettings,
    AudioSettingsBaseModel,
    delete_audio_for_chapters,
    normalize_filename,
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
