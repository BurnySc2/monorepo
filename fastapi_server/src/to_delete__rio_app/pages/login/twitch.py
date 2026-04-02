from __future__ import annotations

import rio

from rio_app.components.login.cookies import (
    LoginSettings,
)
from rio_app.components.login.twitch import twitch_verify_code


@rio.page(
    name="Login with Twitch",
    url_segment="twitch",
)
class CallbackTwitchPage(rio.Component):
    twitch_access_token: rio.HttpOnly[str | None] = None

    @rio.event.on_mount
    async def on_mount(self):
        code = self.session.active_page_url.query.get("code", None)
        if code is None:
            return
        access_token = await twitch_verify_code(code)
        if isinstance(access_token, str):
            login_settings = self.session[LoginSettings]
            login_settings.twitch_access_token = access_token
            self.session.attach(login_settings)
            self.session.navigate_to("/login")

    def build(self) -> rio.Component:
        return rio.Column(rio.ProgressCircle(align_x=0.5))
