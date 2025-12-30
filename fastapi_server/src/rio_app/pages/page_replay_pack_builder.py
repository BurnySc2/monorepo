# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportAttributeAccessIssue=false, reportImplicitOverride=false

import rio

from rio_app.components.replay_pack_builder.filter_component import FilterComponent
from rio_app.components.replay_pack_builder.models import ParsedReplayFile, ReplayFile
from rio_app.components.replay_pack_builder.name_template_component import NameTemplateComponent
from rio_app.components.replay_pack_builder.settings import FilterSettings
from rio_app.components.replay_pack_builder.upload_component import UploadComponent
from rio_app.components.replay_pack_builder.zip_and_download_component import ZipAndDownloadComponent


@rio.page(
    name="Replay Pack Builder",
    url_segment="replay_pack_builder",
)
class ReplayPackBuilderPage(rio.Component):
    uploaded_files: dict[str, ReplayFile] = {}
    parsed_files: dict[str, ParsedReplayFile] = {}
    filtered_replays: list[ParsedReplayFile] = []
    replay_name_pattern: str = r"{date}_{time}_{p1r}v{p2r}_{p1name}_vs_{p2name}_on_{map}"

    @rio.event.periodic(1)
    async def update_filtered_replays(self):
        filter_settings = self.session[FilterSettings]
        if not filter_settings.filtered_replays_need_updating:
            return

        filter_settings.filtered_replays_need_updating = False
        filtered: list[ParsedReplayFile] = []
        for file in self.parsed_files.values():
            if await filter_settings.replay_passes_filter(file):
                filtered.append(file)

        # Filter changed while parsing replays
        if filter_settings.filtered_replays_need_updating:
            return
        self.filtered_replays = filtered
        filter_settings.filtered_replays_need_updating = False
        self.session.attach(filter_settings)

    def build(self) -> rio.Component:
        return rio.Column(
            UploadComponent(self.bind().uploaded_files, self.bind().parsed_files, self.bind().filtered_replays),
            rio.Separator(min_height=0.1, margin_y=0.5),
            FilterComponent(),
            rio.Separator(min_height=0.1, margin_y=0.5),
            NameTemplateComponent(self.bind().replay_name_pattern),
            rio.Separator(min_height=0.1, margin_y=0.5),
            ZipAndDownloadComponent(
                self.bind().uploaded_files,
                self.bind().filtered_replays,
                self.bind().replay_name_pattern,
            ),
            margin=2,
            margin_x=20,
            align_x=0.5,
            align_y=0.5,
        )
