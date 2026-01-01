# pyright: reportImplicitOverride=false
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import arrow
import rio
from pydantic import BaseModel

from minio_helper import SC2_REPLAYS_BUCKET, get_s3_client, object_create_presigned_url, object_download, object_upload
from rio_app.components.replay_pack_builder.models import ParsedReplayFile, ReplayFile
from rio_app.components.replay_pack_builder.settings import FilterSettings


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

    def rename_file_according_to_template(self, replay: ParsedReplayFile) -> str:
        class Player(BaseModel):
            name: str
            race: str
            mmr: int | None

        player1 = Player(name="", race=" ", mmr=None)
        player2 = Player(name="", race=" ", mmr=None)
        for i1, team in enumerate(replay.teams):
            for _, player in enumerate(team.players):
                if i1 == 0:
                    player1 = Player(name=player.name, race=player.play_race, mmr=player.mmr or 0)
                elif i1 == 1:
                    player2 = Player(name=player.name, race=player.play_race, mmr=player.mmr or 0)

        datetime = arrow.get(replay.played_timestamp)
        minutes, seconds = [replay.game_length_seconds // 60, replay.game_length_seconds % 60]
        placeholders = {
            "date": datetime.format("YYYY_MM_DD"),
            "time": datetime.format("hh_mm_ss"),
            "duration": f"{minutes}m {seconds:02d}s",
            "map": replay.map_name.replace(" ", "_"),
            "region": replay.region_short,
            "REGION": replay.region_short.upper(),
            "version": replay.game_version,
            "p1name": player1.name,
            "p1race": player1.race,
            "p1r": player1.race[0],
            "p1mmr": player1.mmr,
            "p2name": player2.name,
            "p2race": player2.race,
            "p2r": player2.race[0],
            "p2mmr": player2.mmr,
        }
        new_name = self.replay_name_pattern
        for placeholder, value in placeholders.items():
            new_name = new_name.replace(f"{{{placeholder}}}", f"{value}")
        return new_name

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
                    new_name = self.rename_file_according_to_template(replay_data)
                    data = await object_download(s3, SC2_REPLAYS_BUCKET, replay_data.minio_key)
                    if data is None:
                        continue
                    zipfile_handler.writestr(f"{new_name}.SC2Replay", data)

        # Create zip, upload to minio, then redirect to pre-signed url
        async with get_s3_client() as s3:
            key = f"replaypack/{self.user_id}"
            await object_upload(s3, SC2_REPLAYS_BUCKET, key, zip_buffer.getvalue())
            url = await object_create_presigned_url(s3, SC2_REPLAYS_BUCKET, key, file_name="replay_pack.zip")
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
