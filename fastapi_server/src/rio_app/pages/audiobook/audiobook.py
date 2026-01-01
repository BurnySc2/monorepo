# pyright: reportImplicitOverride=false

import rio

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
    # TODO On file drop: redirect to page of the book
    # TODO List already uploaded books
    # TODO Clicking on book redirects to book page
    # TODO Allow user to delete book from the list
    # TODO Add button to delete all books
    def build(self):
        return rio.Column(
            rio.Text("Audiobooks", style="heading1", font_weight="bold", align_x=0.5),
            rio.FilePickerArea(),
            rio.Table(data=data, show_row_numbers=False),
            align_x=0.5,
            align_y=0.5,
            spacing=1,
        )
