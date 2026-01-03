# pyright: reportImplicitOverride=false

import rio


@rio.page(name="Login", url_segment="login")
class LoginPage(rio.Component):
    def build(self) -> rio.Component:
        return rio.Row(
            # The PageView is responsible for displaying
            # the currently active sub-page
            rio.PageView(),
        )
