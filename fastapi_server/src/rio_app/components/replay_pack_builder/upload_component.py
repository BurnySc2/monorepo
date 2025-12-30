# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportAttributeAccessIssue=false, reportImplicitOverride=false
from io import BytesIO

import rio
from loguru import logger
from rio.components.file_picker_area import FilePickerArea

from rio_app.components.replay_pack_builder.models import ParsedReplayFile, ReplayData, ReplayFile
from rio_app.components.replay_pack_builder.replay_parser import parse_replay
from rio_app.components.replay_pack_builder.settings import FilterSettings


class UploadComponent(rio.Component):
    uploaded_files: dict[str, ReplayFile] = {}
    parsed_files: dict[str, ParsedReplayFile] = {}
    filtered_replays: list[ParsedReplayFile] = []

    def clear_files(self):
        self.uploaded_files = {}
        self.parsed_files = {}
        self.filtered_replays = []

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

    async def parse_replays(self, _event: rio.FilePickEvent):
        if self.file_picker is None:
            return
        # Add newly added replays
        for new_file in self.file_picker.files:
            replay_file = ReplayFile(
                file_name=new_file.name,
                data=await new_file.read_bytes(),
                status="uploaded",
            )
            replay_file_md5 = replay_file.md5
            # Already parsed, duplicate
            if replay_file_md5 in self.uploaded_files or replay_file_md5 in self.parsed_files:
                continue
            self.uploaded_files[replay_file_md5] = replay_file
        # Clear list in file_picker
        self.file_picker.files = []
        # self.force_refresh()

        # Parse newly added replays
        for replay_file_md5 in list(self.uploaded_files):
            replay_file = self.uploaded_files.get(replay_file_md5, None)
            if replay_file is None:
                continue
            if replay_file.status != "uploaded":
                continue
            try:
                replay_file.status = "processing"
                replay_data: ReplayData = await parse_replay(BytesIO(replay_file.data))
                self.parsed_files[replay_file_md5] = ParsedReplayFile(
                    **replay_file.model_dump(),  # pyright: ignore[reportAny]
                    **replay_data.model_dump(),
                )
                _ = self.uploaded_files.pop(replay_file_md5)
                replay_file.status = "processed"
            except Exception as e:  # noqa: BLE001
                replay_file.status = "error"
                logger.info(f"Error parsing replay file {e}")

        filter_settings = self.session[FilterSettings]
        filter_settings.filtered_replays_need_updating = True
        self.session.attach(filter_settings)

    def build(self) -> rio.Component:
        component = rio.Column(
            rio.Text("Upload Replays", style="heading1"),
        )
        if 0 < self.uploaded_replays_count:
            _ = component.add(rio.Button("Clear uploaded files", on_press=self.clear_files, align_x=0))
        _ = component.add(rio.Text(f"Total replays uploaded: {self.uploaded_replays_count}"))
        _ = component.add(
            rio.FilePickerArea(
                "Drop your replay files here",
                on_pick_file=self.parse_replays,
                file_types=["SC2Replay"],
                multiple=True,
            )
        )
        return component
