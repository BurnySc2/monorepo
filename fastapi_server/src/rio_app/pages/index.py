import rio


@rio.page(
    name="Burnysc2's Website",
    url_segment="",
)
class ReplayPackBuilderPage(rio.Component):
    def build(self) -> rio.Component:
        return rio.Text("Hello world!")
