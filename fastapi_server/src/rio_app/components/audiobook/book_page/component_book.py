import rio

from models.audiobook import AudiobookBook


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
                    style="heading2",
                    align_x=1,  # pyrefly: ignore
                )
            )
        row_book_author.children.append(
            rio.IconButton("material/edit_square", align_x=1, style="colored-text", on_press=self.on_edit_author_button)
        )

        return rio.Column(row_book_title, row_book_author)
