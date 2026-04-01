from io import BytesIO

import rio
from loguru import logger

from minio_helper import (
    MINIO_SC2_REPLAYS_BUCKET,
    bucket_list_objects,
    get_s3_client,
    object_delete,
    object_download,
    object_upload,
    objects_delete_with_prefix,
)
from rio_app.components.replay_pack_builder.models import (
    ParsedReplayFile,
    ReplayData,
    ReplayFile,
)
from rio_app.components.replay_pack_builder.replay_parser import parse_replay
from rio_app.components.replay_pack_builder.settings import FilterSettings


class UploadComponent(rio.Component):
    # md5 as key
    uploaded_files: dict[str, ReplayFile] = {}
    parsed_files: dict[str, ParsedReplayFile] = {}
    filtered_replays: list[ParsedReplayFile] = []
    on_update_filters: rio.EventHandler[[]] = None

    file_picker_files: list[rio.FileInfo] = []
    user_id: str = ""

    @rio.event.on_mount
    async def on_mount(self):
        filter_settings = self.session[FilterSettings]
        self.user_id = filter_settings.user_id
        async with get_s3_client() as s3:
            replays_by_user = await bucket_list_objects(s3, MINIO_SC2_REPLAYS_BUCKET, self.user_id)
        for replay_response in replays_by_user:
            replay = ReplayFile.from_minio(replay_response)
            self.uploaded_files[replay.md5] = replay
        self.force_refresh()
        await self.process_replays()

    async def clear_files(self):
        self.uploaded_files = {}
        self.parsed_files = {}
        self.filtered_replays = []
        # Delete all files in minio by user_id
        if self.user_id != "":
            await objects_delete_with_prefix(MINIO_SC2_REPLAYS_BUCKET, self.user_id)

    @property
    def uploaded_replays_count(self):
        return len(self.uploaded_files) + len(self.parsed_files)

    async def handle_replays_upload(self, _event: rio.FilePickEvent):
        # Add newly added replays
        for new_file in self.file_picker_files:
            # 100 mb file size limit
            if 100 * 2**30 < new_file.size_in_bytes:
                continue
            data = await new_file.read_bytes()
            replay_file = ReplayFile.from_file_info(self.user_id, new_file, data)
            # Already parsed, duplicate
            if replay_file.md5 in self.uploaded_files or replay_file.md5 in self.parsed_files:
                continue
            async with get_s3_client() as s3:
                await object_upload(s3, MINIO_SC2_REPLAYS_BUCKET, replay_file.minio_key, data)
            self.uploaded_files[replay_file.md5] = replay_file
        # Clear list in file_picker
        self.file_picker_files.clear()
        self.force_refresh()
        await self.process_replays()

    async def process_replays(self):
        # Parse newly added replays
        filter_settings = self.session[FilterSettings]
        for replay_file_md5 in list(self.uploaded_files):
            replay_file = self.uploaded_files.get(replay_file_md5, None)
            if replay_file is None:
                continue
            if replay_file.status != "uploaded":
                continue
            try:
                replay_file.status = "processing"
                # Get bytes from minio object
                async with get_s3_client() as s3:
                    replay_by_user = await object_download(s3, MINIO_SC2_REPLAYS_BUCKET, replay_file.minio_key)
                if replay_by_user is None:
                    raise ValueError("Replay does not exist")
                replay_data: ReplayData = await parse_replay(BytesIO(replay_by_user))
                self.parsed_files[replay_file_md5] = ParsedReplayFile(
                    **replay_file.model_dump(),
                    **replay_data.model_dump(),
                )
                _ = self.uploaded_files.pop(replay_file_md5)
                self.parsed_files[replay_file_md5].status = "processed"
            except Exception as e:  # noqa: BLE001
                async with get_s3_client() as s3:
                    await object_delete(s3, MINIO_SC2_REPLAYS_BUCKET, replay_file.minio_key)
                _ = self.uploaded_files.pop(replay_file.md5, None)
                logger.info(f"Error parsing replay file {e}")
        self.session.attach(filter_settings)
        await self.call_event_handler(self.on_update_filters)

    def build(self) -> rio.Component:
        component = rio.Column(
            rio.Text("Upload Replays", style="heading1"),
        )
        if 0 < self.uploaded_replays_count:
            component.children.append(rio.Button("Remove uploaded files", on_press=self.clear_files, align_x=0))
        component.children.extend(
            [
                rio.Text(f"Total replays uploaded: {self.uploaded_replays_count}"),
                rio.FilePickerArea(
                    "Drop your replay files here",
                    on_pick_file=self.handle_replays_upload,
                    files=self.bind().file_picker_files,
                    file_types=["SC2Replay"],
                    multiple=True,
                ),
            ]
        )
        return component
