from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import rio
from dotenv import load_dotenv

from minio_helper import AUDIOBOOK_BUCKET, SC2_REPLAYS_BUCKET, bucket_create, bucket_set_expiration, get_s3_client
from models.audiobook import AudiobookBook, AudiobookChapter
from rio_app import data_models, theme
from rio_app.components.audiobook.models import AudioSettings
from rio_app.components.login.cookies import LoggedInUser, LoginSettings, provide_logged_in_user
from rio_app.components.replay_pack_builder.settings import FilterSettings
from rio_app.components.tts.tts_settings import TTSSettings
from rio_app.routes.index import router

_ = load_dotenv()

assert os.getenv("STAGE", "dev") in {"local_dev", "dev", "prod", "test"}, os.getenv("STAGE")
# pyrefly: ignore
STAGE: Literal["local_dev", "dev", "prod", "test"] = os.getenv("STAGE")


async def on_app_start(_app: rio.App):
    # TODO Create database tables
    # Create minio buckets
    async with get_s3_client() as s3:
        await bucket_create(s3, SC2_REPLAYS_BUCKET)
        await bucket_set_expiration(s3, SC2_REPLAYS_BUCKET, 1)
        await bucket_create(s3, AUDIOBOOK_BUCKET)
        await bucket_set_expiration(s3, AUDIOBOOK_BUCKET, 21)

    # Create tables
    if STAGE == "dev":
        await AudiobookBook.create_table(if_not_exists=True)
        await AudiobookChapter.create_table(if_not_exists=True)


async def on_session_start(session: rio.Session) -> None:
    # Determine which layout to use
    if session.window_width < 60:
        layout = data_models.PageLayout(
            device="mobile",
        )
    else:
        layout = data_models.PageLayout(
            device="desktop",
        )

    # Attach the layout to the session
    session.attach(layout)

    try:
        logged_in_user = session[LoggedInUser]
    except KeyError:
        login_settings = session[LoginSettings]
        logged_in_user = await provide_logged_in_user(login_settings)
        if logged_in_user is not None:
            session.attach(logged_in_user)


# Create the Rio app
app = rio.App(
    name="Burnysc2's Website",
    # This function will be called each time a user connects
    on_session_start=on_session_start,
    on_app_start=on_app_start,
    # You can optionally provide a root component for the app. By default,
    # Rio's default navigation is used. By providing your own component, you
    # can create components which stay put while the user navigates between
    # pages, such as a navigation bar or footer.
    #
    # When you do this, make sure your component contains a `rio.PageView`
    # so the currently active page is still visible.
    # build=comps.RootComponent,
    # You can also provide a custom theme for the app. This theme will
    # override Rio's default.
    theme=theme.THEME,
    assets_dir=Path(__file__).parent / "assets",
    default_attachments=[FilterSettings(), LoginSettings(), AudioSettings(), TTSSettings()],
)

fastapi_app = app.as_fastapi()
fastapi_app.include_router(router, prefix="/api")
