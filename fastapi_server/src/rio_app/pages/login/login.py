import httpx
import rio

from rio_app.components.login.cookies import (
    BACKEND_SERVER_URL,
    GITHUB_CLIENT_ID,
    TWITCH_CLIENT_ID,
    LoggedInUser,
    LoginSettings,
)
from rio_app.components.login.github import github_get_user
from rio_app.components.login.twitch import twitch_get_user


@rio.page(
    name="Login",
    url_segment="",
)
class LoginRootPage(rio.Component):
    _is_loading: bool = True
    logged_in_user: LoggedInUser | None = None

    @rio.event.on_mount
    async def on_mount(self):
        login_settings = self.session[LoginSettings]

        user = None
        user = await twitch_get_user(login_settings.twitch_access_token)
        if user is None:
            user = await github_get_user(login_settings.github_access_token)

        self.logged_in_user = LoggedInUser.from_service(user)
        self._is_loading = False

    async def twitch_login_handler(self):
        self.session.navigate_to(
            str(
                httpx.URL(
                    "https://id.twitch.tv/oauth2/authorize",
                    params={
                        "client_id": TWITCH_CLIENT_ID,
                        "redirect_uri": f"{BACKEND_SERVER_URL}/login/twitch",
                        "response_type": "code",
                        "scope": "user:read:email",
                    },
                )
            ),
        )

    async def github_login_handler(self):
        self.session.navigate_to(
            str(
                httpx.URL(
                    "https://github.com/login/oauth/authorize",
                    params={
                        "client_id": GITHUB_CLIENT_ID,
                        "scope": "read:user",
                    },
                )
            ),
        )

    async def logout_handler(self):
        login_settings = self.session[LoginSettings]
        login_settings.twitch_access_token = None
        login_settings.github_access_token = None
        login_settings.google_access_token = None
        self.session.attach(login_settings)
        self.logged_in_user = None

    def build(self) -> rio.Component:
        if self._is_loading:
            return rio.ProgressCircle(
                align_x=0.5,
                align_y=0.5,
            )
        if self.logged_in_user is not None:
            return rio.Column(
                rio.Text(
                    f"You are logged in via {self.logged_in_user.service.capitalize()} as '{self.logged_in_user.name}'"
                ),
                rio.Button("Log out", color="danger", on_press=self.logout_handler),
                align_x=0.5,
                align_y=0.5,
                spacing=2,
            )
        return rio.Column(
            rio.Button(
                "Login with Twitch",
                on_press=self.twitch_login_handler,
                icon="brand/twitch",
                color=rio.Color.from_hex("6441a5"),
            ),
            rio.Button(
                "Login with GitHub",
                on_press=self.github_login_handler,
                icon="brand/github",
                color=rio.Color.from_hex("171515"),
            ),
            rio.Button(
                "Login with Google",
                on_press=self.twitch_login_handler,
                icon="brand/google",
                color=rio.Color.from_hex("4285F4"),
            ),
            align_x=0.5,
            align_y=0.5,
            spacing=2,
        )
