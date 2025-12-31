# pyright: reportImplicitOverride=false
from __future__ import annotations

import rio


@rio.page(
    name="Login with GitHub",
    url_segment="github",
)
class CallbackGitHubPage(rio.Component):
    def build(self) -> rio.Component:
        return rio.Text("TODO")
