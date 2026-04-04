from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import rio
from rio_app.components.replay_pack_builder.models import ParsedReplayFile, ReplayFile
from rio_app.components.replay_pack_builder.settings import FilterSettings

from minio_helper import (
    GARAGE_SC2_REPLAYS_BUCKET,
    get_s3_client,
    object_create_presigned_url,
    object_download,
    object_upload,
)


class ZipAndDownloadComponent(rio.Component):
    uploaded_files: dict[str, ReplayFile] = {}
    filtered_replays: list[ParsedReplayFile] = []
    replay_name_pattern: str = ""

    user_id: str = ""

    @rio.event.on_mount
    async def on_mount(self):
        filter_settings = self.session[FilterSettings]
        self.user_id = filter_settings.user_id

    @property
    def replays_processing_count(self) -> int:
        return sum(1 for file in self.uploaded_files.values() if file.status in ["uploaded", "processing"])

    async def handle_download(self):
        if self.user_id == "":
            return
        if len(self.filtered_replays) == 0:
            return
        # Create zip file
        # TODO Add spinner while zipping

        # TODO Zip and stream upload using https://stream-zip.docs.trade.gov.uk/async-interface/
        zip_buffer = BytesIO()
        async with get_s3_client() as s3:
            with ZipFile(zip_buffer, "w", ZIP_DEFLATED, False) as zipfile_handler:
                for replay_data in self.filtered_replays:
                    new_name = replay_data.rename_file_according_to_template(self.replay_name_pattern)
                    data = await object_download(s3, GARAGE_SC2_REPLAYS_BUCKET, replay_data.minio_key)
                    if data is None:
                        continue
                    zipfile_handler.writestr(f"{new_name}.SC2Replay", data)

        # Create zip, upload to minio, then redirect to pre-signed url
        async with get_s3_client() as s3:
            key = f"replaypack/{self.user_id}"
            await object_upload(s3, GARAGE_SC2_REPLAYS_BUCKET, key, zip_buffer.getvalue())
            url = await object_create_presigned_url(s3, GARAGE_SC2_REPLAYS_BUCKET, key, file_name="replay_pack.zip")
            if url is None:
                return
        self.session.open_url_in_browser(url)
        # await self.session.save_file(zip_buffer.getvalue(), "replay_pack.zip")

    def build(self) -> rio.Component:
        col = rio.Column()
        if 0 < self.replays_processing_count:
            _ = col.add(
                rio.Row(
                    rio.Text(f"Processing: {self.replays_processing_count}"),
                    rio.ProgressCircle(
                        (len(self.uploaded_files) - self.replays_processing_count) / len(self.uploaded_files)
                    ),
                )
            )
        # Disable button if no replays to download: none passing filters
        button_enabled = self.replays_processing_count == 0 and 0 < len(self.filtered_replays)
        btn = rio.Button(
            "Zip and download replays",
            on_press=self.handle_download,
            is_sensitive=button_enabled,
            icon="material/download",
        )
        if 0 < len(self.filtered_replays):
            btn.content = f"Zip and download {len(self.filtered_replays)} replays"
        _ = col.add(btn)
        return col
