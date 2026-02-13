import rio


@rio.page(name="Audiobook converter", url_segment="audiobook")
class AudiobookPage(rio.Component):
    def build(self) -> rio.Component:
        return rio.Row(
            # The PageView is responsible for displaying
            # the currently active sub-page
            rio.PageView(),
        )
