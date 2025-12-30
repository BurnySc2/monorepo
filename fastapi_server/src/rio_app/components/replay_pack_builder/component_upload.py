# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportAttributeAccessIssue=false, reportImplicitOverride=false
import shutil
from io import BytesIO
from pathlib import Path

import rio
from loguru import logger
from rio.components.file_picker_area import FilePickerArea

from rio_app.components.replay_pack_builder.models import (
    FILES_IN_ORDER,
    REPLAYS_FOLDER,
    ParsedReplayFile,
    ReplayData,
    ReplayFile,
    quota,
)
from rio_app.components.replay_pack_builder.replay_parser import parse_replay
from rio_app.components.replay_pack_builder.settings import FilterSettings




def delete_file(path: Path):
    global quota_usage
    if path.is_file():
        quota["quota_usage"] -= path.stat().st_size
    path.unlink(missing_ok=True)


class UploadComponent(rio.Component):
    # md5 as key
    uploaded_files: dict[str, ReplayFile] = {}
    parsed_files: dict[str, ParsedReplayFile] = {}
    filtered_replays: list[ParsedReplayFile] = []

    @rio.event.on_mount
    async def on_mount(self):
        filter_settings = self.session[FilterSettings]
        for p in (REPLAYS_FOLDER / filter_settings.user_id).glob("*.SC2Replay"):
            replay = ReplayFile.from_file(p)
            self.uploaded_files[replay.md5] = replay
        self.session.attach(filter_settings)
        await self.process_replays()

    def clear_files(self):
        self.uploaded_files = {}
        self.parsed_files = {}
        self.filtered_replays = []
        # Delete replay files for user
        filter_settings = self.session[FilterSettings]
        user_path = REPLAYS_FOLDER / filter_settings.user_id
        shutil.rmtree(user_path)

    @property
    def uploaded_replays_count(self):
        return len(self.uploaded_files) + len(self.parsed_files)

    @property
    def file_picker(self) -> FilePickerArea | None:
        try:
            my_file_picker = next(
                (i for i in self._build_data_.all_children_in_build_boundary if isinstance(i, FilePickerArea)),  # pyright: ignore[reportOptionalMemberAccess]
                None,
            )
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error with file picker: {e}")
            return None
        return my_file_picker

    async def handle_replays_upload(self, _event: rio.FilePickEvent):
        if self.file_picker is None:
            return
        filter_settings = self.session[FilterSettings]
        # Delete if above quota
        for p in list(FILES_IN_ORDER):
            if quota["quota_usage"] < quota["QUOTA_LIMIT"]:
                break
            delete_file(p)
            _ = FILES_IN_ORDER.popleft()

        # Add newly added replays
        for new_file in self.file_picker.files:
            data = await new_file.read_bytes()
            replay_file = ReplayFile.from_file_info(new_file, data)
            # Already parsed, duplicate
            if replay_file.md5 in self.uploaded_files or replay_file.md5 in self.parsed_files:
                continue
            quota["quota_usage"] += replay_file.save_to_disk(filter_settings.user_id, data)
            if replay_file.path:
                FILES_IN_ORDER.append(replay_file.path)
            self.uploaded_files[replay_file.md5] = replay_file
        # Clear list in file_picker
        self.file_picker.files = []
        # self.force_refresh()
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
                replay_data: ReplayData = await parse_replay(BytesIO(replay_file.read_file()))
                self.parsed_files[replay_file_md5] = ParsedReplayFile(
                    **replay_file.model_dump(),  # pyright: ignore[reportAny]
                    **replay_data.model_dump(),
                )
                _ = self.uploaded_files.pop(replay_file_md5)
                self.parsed_files[replay_file_md5].status = "processed"
            except Exception as e:  # noqa: BLE001
                replay_file.status = "error"
                logger.info(f"Error parsing replay file {e}")
        filter_settings.filtered_replays_need_updating = True
        self.session.attach(filter_settings)

    def build(self) -> rio.Component:
        component = rio.Column(
            rio.Text("Upload Replays", style="heading1"),
        )
        if 0 < self.uploaded_replays_count:
            _ = component.add(rio.Button("Remove uploaded files", on_press=self.clear_files, align_x=0))
        _ = component.add(rio.Text(f"Total replays uploaded: {self.uploaded_replays_count}"))

        _ = component.add(
            rio.FilePickerArea(
                "Drop your replay files here",
                on_pick_file=self.handle_replays_upload,
                file_types=["SC2Replay"],
                multiple=True,
            )
        )
        return component
