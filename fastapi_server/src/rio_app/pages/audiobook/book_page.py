# pyright: reportImplicitOverride=false

import rio

from rio_app.components.audiobook.models import Book, Chapter

data = {
    "Name": ["Alice", "Bob", "Charlie"],
    "Age": [25, 30, 35],
    "City": ["New York", "San Francisco", "Los Angeles"],
}


class BookComponent(rio.Component):
    book: Book

    def build(self):
        # TODO After clicking on edit, allow user to change title and author name
        return rio.Column(
            rio.Row(
                # pyrefly: ignore
                rio.Text(f"{self.book.title}", style="heading1", align_x=1),
                rio.IconButton("material/edit_square", align_x=0, style="colored-text"),
                spacing=1,
            ),
            rio.Row(
                # pyrefly: ignore
                rio.Text(f"{self.book.author}", style="heading1", align_x=1),
                rio.IconButton("material/edit_square", align_x=0, style="colored-text"),
                spacing=1,
            ),
        )


class AudiobookSettingsComponent(rio.Component):
    chapters: list[Chapter]

    @property
    def is_button_generate_audio_enabled(self) -> bool:
        return any(not (c.queued or c.audio_generated) for c in self.chapters)

    @property
    def is_button_download_enabled(self) -> bool:
        return all(c.audio_generated for c in self.chapters)

    @property
    def button_download_has_spinner(self) -> bool:
        return any(c.queued for c in self.chapters)

    def build(self):
        return rio.Rectangle(
            content=rio.Column(
                # pyrefly: ignore
                rio.Text("Settings", style="heading2", align_x=0.5),
                # TODO Allow user to change voice
                # TODO Grab all available voices from edge-tts
                # TODO Store voice settings in localstorage
                rio.Grid(
                    # pyrefly: ignore
                    [rio.Text("Voice", align_x=1), rio.Dropdown({"Hallo": "Welt"})],
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
                        grow_x=True,  # pyrefly: ignore
                    ),
                    rio.Button(
                        "Download book",
                        color="primary",
                        is_loading=self.button_download_has_spinner,
                        is_sensitive=self.is_button_download_enabled,
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
    chapter: Chapter

    # TODO Generate audio event handler
    # TODO Delete audio event handler
    # TODO Download audio event handler

    def build(self):
        row = rio.Row(
            spacing=0.5,
        )
        if self.chapter.audio_generated:
            row.children.extend(
                [
                    rio.Webview(
                        self.chapter.audio_url,
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
                    ),
                ]
            )

        elif self.chapter.queued:
            if 0 < self.chapter.queued_position:
                row.children.extend(
                    [
                        rio.ProgressCircle(align_x=1),
                        rio.Text(
                            f"Queued ({self.chapter.queued_position})",
                            align_x=1,  # pyrefly: ignore
                        ),
                    ]
                )
            else:
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
                ),
            )
        else:
            row.children.append(rio.Button("Generate audio", color="success"))
        return row


@rio.page(
    name="TODO according to book",
    url_segment="book/{book_id}",
)
class AudiobookBookPage(rio.Component):
    book_id: int

    # book: Book | None = None
    # chapters: list[Chapter] = []

    book: Book = Book(
        id=0,
        chapters_count=0,
        title="Hallo ChefuBr0t",
        author="BurnySc2",
    )
    chapters: list[Chapter] = [
        Chapter(
            id=0,
            number=1,
            title="Mein tolles Kapitel1",
            word_count=0,
            sentence_count=7,
            queued=True,
            queued_position=5,
            audio_generated=True,
            audio_url=TEST_HTML,
        ),
        Chapter(
            id=0,
            number=1,
            title="Mein tolles Kapitel2",
            word_count=0,
            sentence_count=7,
            queued=True,
            queued_position=5,
            audio_generated=False,
            audio_url="",
        ),
        Chapter(
            id=0,
            number=1,
            title="Mein tolles Kapitel3         asdasd",
            word_count=0,
            sentence_count=8,
            queued=False,
            queued_position=5,
            audio_generated=False,
            audio_url="",
        ),
    ]

    @rio.event.on_mount
    async def on_mount(self):
        # TODO Get data from database about book and chapters
        # TODO Get audiosettings from localstorage
        pass

    def build(self):
        my_grid: list[list[rio.Component]] = []
        for chapter in self.chapters:
            my_grid.append(
                [
                    rio.Text(
                        f"'{chapter.custom_title or chapter.title}' with {chapter.sentence_count} sentences",
                        grow_x=True,  # pyrefly: ignore
                        overflow="wrap",
                    ),
                    AudiobookChapterComponent(chapter),
                ]
            )

        return rio.Column(
            BookComponent(self.book),
            # TODO Pass down audiosettings (binding)
            AudiobookSettingsComponent(self.chapters),
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
