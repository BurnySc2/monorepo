# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportAttributeAccessIssue=false, reportImplicitOverride=false
from dataclasses import dataclass
from hashlib import md5
from io import BytesIO
from rio.components.file_picker_area import FilePickerArea
from typing import Literal
from zipfile import ZIP_DEFLATED, ZipFile

import arrow
import sc2reader  # pyright: ignore[reportMissingTypeStubs]
from loguru import logger
from pydantic import BaseModel
from sc2reader.resources import Replay  # pyright: ignore[reportMissingTypeStubs]
import rio


@dataclass
class ReplayPlayer:
    clan_tag: str  # Empty string if not in clan
    name: str
    pick_race: Literal["Random", "Protoss", "Terran", "Zerg"]
    play_race: Literal["Protoss", "Terran", "Zerg"]
    is_human: bool
    mmr: int | None  # Only visible in ranked match


@dataclass
class ReplayTeam:
    result: Literal["Win", "Loss"] | None
    players: list[ReplayPlayer]


class ReplayFile(BaseModel):
    file_name: str
    data: bytes
    status: Literal["uploaded", "processing", "processed", "error"] = "uploaded"

    @property
    def md5(self) -> str:
        return md5(self.data).hexdigest()


class ParsedReplayFile(ReplayFile):
    # Per player data
    teams: list[ReplayTeam]

    played_timestamp: int
    game_length_seconds: int
    map_name: str
    region_short: Literal["us", "eu", "kr", "cn"]
    expansion: Literal["WoL", "HotS", "LotV"]
    game_base_build: int
    game_version: str
    game_type: str
    is_ladder: bool
    is_private: bool
    resume_from_replay: bool
    # chat_messages: list[ReplayMessage]


class ReplayData(BaseModel):
    teams: list[ReplayTeam]
    played_timestamp: int
    game_length_seconds: int
    map_name: str
    region_short: Literal["us", "eu", "kr", "cn"]
    expansion: Literal["WoL", "HotS", "LotV"]
    game_base_build: int
    game_version: str
    game_type: str
    is_ladder: bool
    is_private: bool
    resume_from_replay: bool
    # chat_messages: list[ReplayMessage]


async def parse_replay(data: BytesIO) -> ReplayData:
    replay: Replay = sc2reader.load_replay(data, load_level=2)  # pyright: ignore[reportUnknownVariableType]
    parsed = {  # pyright: ignore[reportUnknownVariableType]
        "teams": [
            {
                "result": team.result,
                "players": [
                    {
                        # May not be set on computer
                        "clan_tag": player.__dict__.get("clan_tag", ""),
                        "name": player.name,
                        "pick_race": player.pick_race,
                        "play_race": player.play_race,
                        "is_human": player.is_human,
                        # init_data is not set on computer
                        "mmr": player.__dict__.get("init_data", {}).get("scaled_rating", None),
                    }
                    for player in team.players  # pyright: ignore[reportUnknownVariableType]
                ],
            }
            for team in replay.teams  # pyright: ignore[reportUnknownVariableType]
        ],
        "is_ladder": replay.is_ladder,
        "is_private": replay.is_private,
        "resume_from_replay": replay.resume_from_replay,
        "played_timestamp": replay.unix_timestamp * 1000,
        "game_length_seconds": replay.length.seconds,  # pyright: ignore[reportOptionalMemberAccess]
        "game_base_build": replay.base_build,
        "game_version": ".".join(map(str, replay.versions[1:4])),
        "game_type": replay.type,
        "map_name": replay.map_name,
        "region_short": replay.region,
        "expansion": replay.expansion,
    }
    parsed_checked = ReplayData(**parsed)  # pyright: ignore[reportArgumentType]  # ty:ignore[invalid-argument-type]
    return parsed_checked


class FilterSettings(rio.UserSettings):
    filter_enabled: bool = True
    game_matchmaking: bool = True
    game_custom: bool = True
    game_coop: bool = True
    game_arcade: bool = True
    game_include_games_with_ai: bool = False
    game_include_games_resumed_from_replay: bool = False
    expansion_wol: bool = True
    expansion_hots: bool = True
    expansion_lotv: bool = True
    server_americas: bool = True
    server_europe: bool = True
    server_asia: bool = True
    # Unable do store as date (can't convert to JSON bug?)
    date_played_min: float = arrow.get("2010-01-01").timestamp()
    date_played_max: float = arrow.utcnow().timestamp()
    game_duration_min: int = 0
    game_duration_max: int = 9999
    player_count_min: int = 2
    player_count_max: int = 2
    average_mmr_min: int = 0
    average_mmr_max: int = 9999
    matchup_pvp: bool = True
    matchup_pvt: bool = True
    matchup_pvz: bool = True
    matchup_tvt: bool = True
    matchup_tvz: bool = True
    matchup_zvz: bool = True
    player_name_must_include: str = ""
    player_name_must_exclude: str = ""
    map_name_must_include: str = ""
    map_name_must_exclude: str = ""

    filtered_replays_need_updating: bool = False

    async def replay_passes_filter(self, replay: ParsedReplayFile) -> bool:
        if not self.filter_enabled:
            return True
        if not self.game_matchmaking and replay.is_ladder:
            return False
        if not self.game_custom and replay.is_private:
            return False
        # TODO Coop and arcade replays
        has_computers = any(not player.is_human for team in replay.teams for player in team.players)
        if not self.game_include_games_with_ai and has_computers:
            return False
        if not self.game_include_games_resumed_from_replay and replay.resume_from_replay:
            return False
        # Expansion
        if any(
            [
                not self.expansion_wol and replay.expansion == "WoL",
                not self.expansion_hots and replay.expansion == "HotS",
                not self.expansion_lotv and replay.expansion == "LotV",
            ]
        ):
            return False
        # Server
        if not self.server_americas and replay.region_short == "us":
            return False
        if not self.server_europe and replay.region_short == "eu":
            return False
        if not self.server_asia and replay.region_short == "kr":
            return False

        # Date played filter
        game_date = arrow.get(replay.played_timestamp).timestamp()
        if not (self.date_played_min <= game_date <= self.date_played_max):
            return False

        # Game duration filter
        if not (self.game_duration_min <= replay.game_length_seconds <= self.game_duration_max):
            return False

        # Average mmr filter
        average_mmr = sum(player.mmr for team in replay.teams for player in team.players if player.mmr is not None)
        if not (self.average_mmr_min <= average_mmr <= self.average_mmr_max):
            return False

        # Player count filter
        teams_count = len(replay.teams)
        players_count = sum(len(team.players) for team in replay.teams)

        # Matchup filter
        if teams_count == 2 and players_count == 2:
            players = [replay.teams[0].players[0], replay.teams[1].players[0]]
            player_races = "v".join(p.play_race[0] for p in sorted(players, key=lambda i: i.play_race))
            if not self.matchup_pvp and player_races == "PvP":
                return False
            if not self.matchup_pvt and player_races == "PvT":
                return False
            if not self.matchup_pvz and player_races == "PvZ":
                return False
            if not self.matchup_tvt and player_races == "TvT":
                return False
            if not self.matchup_tvz and player_races == "TvZ":
                return False
            if not self.matchup_zvz and player_races == "ZvZ":
                return False

        # Player name include / exclude filter
        all_player_names = [player.name.lower() for team in replay.teams for player in team.players]

        players_must_include = [
            i.strip().lower() for i in self.player_name_must_include.strip().split(",") if i.strip()
        ]
        map_name_matches_include = False
        if players_must_include:
            for player_name in all_player_names:
                for search_string in players_must_include:
                    if search_string in player_name:
                        map_name_matches_include = True
            if not map_name_matches_include:
                return False

        players_must_exclude = [
            i.strip().lower() for i in self.player_name_must_exclude.strip().split(",") if i.strip()
        ]
        map_name_matches_exclude = False
        if players_must_exclude:
            for player_name in all_player_names:
                for search_string in players_must_exclude:
                    if search_string in player_name:
                        map_name_matches_exclude = True
            if map_name_matches_exclude:
                return False

        # Map name include / exclude filter
        map_name = replay.map_name.lower()

        map_name_must_include = [i.strip().lower() for i in self.map_name_must_include.strip().split(",") if i.strip()]
        map_name_matches_include = False
        if map_name_must_include:
            for search_string in map_name_must_include:
                if search_string in map_name:
                    map_name_matches_include = True
            if not map_name_matches_include:
                return False

        map_name_must_exclude = [i.strip().lower() for i in self.map_name_must_exclude.strip().split(",") if i.strip()]
        map_name_matches_exclude = False
        if map_name_must_exclude:
            for search_string in map_name_must_exclude:
                if search_string in map_name:
                    map_name_matches_exclude = True
            if map_name_matches_exclude:
                return False
        return True


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


class MyFilter(rio.Component):
    kind: type[rio.Checkbox | rio.NumberInput | rio.TextInput | rio.DateInput]
    label: str
    filter_settings_key: str

    def set_value(
        self,
        event: rio.CheckboxChangeEvent | rio.NumberInputChangeEvent | rio.TextInputChangeEvent | rio.DateChangeEvent,
    ):
        filter_settings = self.session[FilterSettings]
        assert self.filter_settings_key in filter_settings.__dict__, self.filter_settings_key
        if isinstance(event, rio.CheckboxChangeEvent):
            filter_settings.__setattr__(self.filter_settings_key, event.is_on)
        if isinstance(event, rio.NumberInputChangeEvent):
            filter_settings.__setattr__(self.filter_settings_key, event.value)
        if isinstance(event, rio.TextInputChangeEvent):
            filter_settings.__setattr__(self.filter_settings_key, event.text)
        if isinstance(event, rio.DateChangeEvent):
            filter_settings.__setattr__(self.filter_settings_key, arrow.get(event.value).timestamp())
        filter_settings.filtered_replays_need_updating = True
        self.session.attach(filter_settings)

    def build(self) -> rio.Component:
        filter_settings = self.session[FilterSettings]
        if self.kind == rio.Checkbox:
            return rio.Row(
                rio.Checkbox(filter_settings.__getattribute__(self.filter_settings_key), on_change=self.set_value),  # pyright: ignore[reportAny]
                rio.Text(self.label),
                spacing=1,
                align_x=0,
            )
        elif self.kind == rio.NumberInput:
            return rio.NumberInput(
                filter_settings.__getattribute__(self.filter_settings_key),  # pyright: ignore[reportAny]
                on_change=self.set_value,
                decimals=0,
            )
        elif self.kind == rio.TextInput:
            return rio.TextInput(filter_settings.__getattribute__(self.filter_settings_key), on_change=self.set_value)  # pyright: ignore[reportAny]
        elif self.kind == rio.DateInput:
            return rio.DateInput(
                arrow.get(filter_settings.__getattribute__(self.filter_settings_key)).date(),  # pyright: ignore[reportAny]
                on_change=self.set_value,
            )
        return rio.Text("TODO")


class FilterComponent(rio.Component):
    def build(self) -> rio.Component:
        return rio.Column(
            rio.Text("Replay Filters", style="heading1"),
            rio.Tooltip(
                MyFilter(
                    rio.Checkbox,
                    "Filter enabled",
                    "filter_enabled",
                ),
                tip="If unchecked, no replay will be filtered and all replays will be renamed and zipped",
            ),
            rio.Text("Game types", style="heading2"),
            MyFilter(rio.Checkbox, "Matchmaking", "game_matchmaking"),
            MyFilter(rio.Checkbox, "Custom Game", "game_custom"),
            MyFilter(rio.Checkbox, "Include Games with AI", "game_include_games_with_ai"),
            MyFilter(
                rio.Checkbox,
                "Include Games Resumed from Replay",
                "game_include_games_resumed_from_replay",
            ),
            rio.Text("Expansion", style="heading2"),
            MyFilter(rio.Checkbox, "Wings of Liberty", "expansion_wol"),
            MyFilter(rio.Checkbox, "Heart of the Swarm", "expansion_hots"),
            MyFilter(rio.Checkbox, "Legacy of the Void", "expansion_lotv"),
            rio.Text("Server", style="heading2"),
            MyFilter(rio.Checkbox, "Americas", "server_americas"),
            MyFilter(rio.Checkbox, "Europe", "server_europe"),
            MyFilter(rio.Checkbox, "Asia", "server_asia"),
            rio.Text("Date played", style="heading2"),
            rio.Row(
                rio.Text("Between"),
                MyFilter(rio.DateInput, "", "date_played_min", grow_x=True),
                rio.Text("and"),
                MyFilter(rio.DateInput, "", "date_played_max", grow_x=True),
                spacing=0.5,
            ),
            rio.Text("Game duration (seconds)", style="heading2"),
            rio.Row(
                rio.Text("Between"),
                MyFilter(rio.NumberInput, "", "game_duration_min", grow_x=True),
                rio.Text("and"),
                MyFilter(rio.NumberInput, "", "game_duration_max", grow_x=True),
                spacing=0.5,
            ),
            rio.Text("Player count", style="heading2"),
            rio.Row(
                rio.Text("Between"),
                MyFilter(rio.NumberInput, "", "player_count_min", grow_x=True),
                rio.Text("and"),
                MyFilter(rio.NumberInput, "", "player_count_max", grow_x=True),
                spacing=0.5,
            ),
            rio.Text("Average player MMR", style="heading2"),
            rio.Row(
                rio.Text("Between"),
                MyFilter(rio.NumberInput, "", "average_mmr_min", grow_x=True),
                rio.Text("and"),
                MyFilter(rio.NumberInput, "", "average_mmr_max", grow_x=True),
                spacing=0.5,
            ),
            rio.Text("Matchups", style="heading2"),
            rio.Grid(
                [
                    MyFilter(rio.Checkbox, "PvP", "matchup_pvp"),
                    MyFilter(rio.Checkbox, "PvT", "matchup_pvt"),
                    MyFilter(rio.Checkbox, "PvZ", "matchup_pvz"),
                ],
                [
                    MyFilter(rio.Checkbox, "TvT", "matchup_tvt"),
                    MyFilter(rio.Checkbox, "TvZ", "matchup_tvz"),
                    MyFilter(rio.Checkbox, "ZvZ", "matchup_zvz"),
                ],
            ),
            rio.Text("Player name (partial match, case insensitive)", style="heading2"),
            rio.Grid(
                [
                    rio.Text("Must include names"),
                    MyFilter(
                        rio.TextInput,
                        "",
                        "player_name_must_include",
                        grow_x=True,
                    ),
                ],
                [
                    rio.Text("Must exclude names"),
                    MyFilter(
                        rio.TextInput,
                        "",
                        "player_name_must_exclude",
                        grow_x=True,
                    ),
                ],
                column_spacing=1,
            ),
            rio.Text("Map name (partial match, case insensitive)", style="heading2"),
            rio.Grid(
                [
                    rio.Text("Must include names"),
                    MyFilter(
                        rio.TextInput,
                        "",
                        "map_name_must_include",
                        grow_x=True,
                    ),
                ],
                [
                    rio.Text("Must exclude names"),
                    MyFilter(
                        rio.TextInput,
                        "",
                        "map_name_must_exclude",
                        grow_x=True,
                    ),
                ],
                column_spacing=1,
            ),
            spacing=1,
        )


class NameTemplateComponent(rio.Component):
    replay_name_pattern: str = ""

    def build(self) -> rio.Component:
        return rio.Column(
            rio.Text("Name template", style="heading1"),
            rio.Grid(
                [rio.Text("Custom pattern"), rio.TextInput(self.bind().replay_name_pattern)],
                [rio.Text("Preview"), rio.Text(self.replay_name_pattern, overflow="wrap")],
                column_spacing=1,
                row_spacing=1,
                align_x=0,
            ),
        )


class ZipAndDownloadComponent(rio.Component):
    uploaded_files: dict[str, ReplayFile] = {}
    filtered_replays: list[ParsedReplayFile] = []
    replay_name_pattern: str = ""

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
        if len(self.filtered_replays) == 0:
            return
        # Create zip file
        # TODO Add spinner while zipping
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, "w", ZIP_DEFLATED, False) as zipfile_handler:
            for replay_data in self.filtered_replays:
                new_name = self.rename_file_according_to_template(replay_data)
                zipfile_handler.writestr(f"{new_name}.SC2Replay", replay_data.data)
        await self.session.save_file(zip_buffer.getvalue(), "replay_pack.zip")

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
        button_disabled = 0 < self.replays_processing_count
        btn = rio.Button("Zip and download replays", on_press=self.handle_download, is_loading=button_disabled)
        if 0 < len(self.filtered_replays):
            btn.content = f"Zip and download {len(self.filtered_replays)} replays"
        _ = col.add(btn)
        return col


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
