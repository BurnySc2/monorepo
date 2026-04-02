import rio


@rio.page(
    name="Burnysc2's Website",
    url_segment="",
)
class ReplayPackBuilderPage(rio.Component):
    def build(self) -> rio.Component:
        return rio.Text(
            "Welcome to burnysc2's homepage",
            # pyrefly: ignore
            align_x=0.5,
        )
