from __future__ import annotations

import rio


@rio.page(
    name="Login with Google",
    url_segment="google",
)
class CallbackGooglePage(rio.Component):
    def build(self) -> rio.Component:
        return rio.Text("TODO")
