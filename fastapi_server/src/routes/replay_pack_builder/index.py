# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportAttributeAccessIssue=false
from dataclasses import dataclass
from hashlib import md5
from io import BytesIO
from typing import Literal
from zipfile import ZIP_DEFLATED, ZipFile

import arrow
import reflex as rx
import sc2reader
from loguru import logger
from pydantic import BaseModel
from sc2reader.resources import Replay

from routes.replay_pack_builder.index_ import ReplayData


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
    parsed_checked = ReplayData(**parsed)  # pyright: ignore[reportArgumentType]
    return parsed_checked


class State(rx.State):
    uploaded_files: dict[str, ReplayFile] = {}
    parsed_files: dict[str, ParsedReplayFile] = {}
    # filtered: list[ParsedReplayFile] = []
    replay_name_pattern: str = r"{date}_{time}_{p1r}v{p2r}_{p1name}_vs_{p2name}_on_{map}"

    # Filters
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
    date_played_min: str
    date_played_max: str
    game_duration_min: str
    game_duration_max: str
    player_count_min: str = "2"
    player_count_max: str = "2"
    average_mmr_min: str = "0"
    average_mmr_max: str = "9999"
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

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        for file in files:
            data = await file.read()
            replay_file = ReplayFile(file_name=file.name or "", data=data)
            self.uploaded_files[replay_file.md5] = replay_file
        await self.parse_replays()

    async def parse_replays(self):
        for md5_hash, replay_file in self.uploaded_files.items():
            if replay_file.status != "uploaded":
                continue
            try:
                replay_file.status = "processing"
                replay_data: ReplayData = await parse_replay(BytesIO(replay_file.data))
                self.parsed_files[md5_hash] = ParsedReplayFile(
                    **replay_file.model_dump(),
                    **replay_data.model_dump(),
                )
                replay_file.status = "processed"
            except Exception as e:
                replay_file.status = "error"
                logger.info(e)

    @rx.var
    def replays_processing_count(self) -> int:
        return sum(1 for file in self.uploaded_files.values() if file.status in ["uploaded", "processing"])

    # Doesnt seem to work:
    # @rx.var(cache=True)
    # def replays_matching_filter_count(self) -> int:
    #     return self.get_all_filtered_replays

    # TODO Turn this into var and reuse above?
    @rx.var(cache=True)
    async def get_all_filtered_replays(self) -> list[ParsedReplayFile]:
        filtered = [file for file in self.parsed_files.values() if self.replay_passes_filter(file)]
        return filtered

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

    async def zip_filtered_replays(self):
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, "w", ZIP_DEFLATED, False) as zipfile_handler:
            for replay_data in await self.get_all_filtered_replays:
                new_name = self.rename_file_according_to_template(replay_data)
                zipfile_handler.writestr(f"{new_name}.SC2Replay", replay_data.data)
        zip_as_data: bytes = zip_buffer.getvalue()
        return rx.download(data=zip_as_data, filename="replay_pack.zip")

    @rx.event
    def set_date_played_min(self, value: str):
        self.date_played_min = value

    @rx.event
    def set_date_played_max(self, value: str):
        self.date_played_max = value

    # TODO Define setters to get rid of warnings

    def replay_passes_filter(self, replay: ParsedReplayFile) -> bool:
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
        if not self.server_asia and replay.region_short == "kr":  # noqa: SIM103
            return False

        # Date played filter

        # Game duration filter

        # Average mmr filter

        # Player count filter

        # Matchup filter

        # Player name include / exclude filter

        # Map name include / exclude filter

        return True


# For sections
FIELDSET_STYLE = {
    "text-align": "center",
    "border_radius": "10px",
    "border": "1px solid",
    "padding": "5px",
}
# For subsections
FIELDSET_SUB_STYLE = {
    **FIELDSET_STYLE,
    "text-align": "left",
    "border_radius": "5px",
    "padding-left": "10px",
}


def _upload_component() -> rx.Component:
    count_uploaded: int = State.uploaded_files.length()  # pyright: ignore[reportUnknownVariableType]
    return rx.el.fieldset(
        rx.el.legend("Upload Replays"),
        rx.flex(
            rx.text(f"Total replays uploaded: {count_uploaded}"),
            rx.text("Upload zone"),
            rx.upload(
                id="upload",
                on_drop=State.handle_upload(
                    rx.upload_files("upload")  # pyright: ignore[reportArgumentType]
                ),
                width="10px",
                height="10px",
            ),
            direction="column",
        ),
        style=[FIELDSET_STYLE],
    )


def _filter_component() -> rx.Component:
    return rx.el.fieldset(
        rx.el.legend("Replay Filters"),
        rx.flex(
            rx.tooltip(
                rx.checkbox(
                    text="Filter enabled",
                    checked=State.filter_enabled,
                    on_change=State.set_filter_enabled,
                ),
                content="If unchecked, no replay will be filtered and all replays will be renamed and zipped",
            ),
            rx.el.fieldset(
                rx.el.legend("Game types"),
                rx.checkbox(
                    text="Matchmaking",
                    checked=State.game_matchmaking,
                    on_change=State.set_game_matchmaking,
                ),
                rx.checkbox(
                    text="Custom Game",
                    checked=State.game_custom,
                    on_change=State.set_game_custom,
                ),
                style=[FIELDSET_SUB_STYLE],
            ),
            rx.checkbox(
                text="Include Games with AI",
                checked=State.game_include_games_with_ai,
                on_change=State.set_game_include_games_with_ai,
            ),
            rx.checkbox(
                text="Include Games Resumed from Replay",
                checked=State.game_include_games_resumed_from_replay,
                on_change=State.set_game_include_games_resumed_from_replay,
            ),
            rx.el.fieldset(
                rx.el.legend("Expansion"),
                rx.checkbox(
                    text="Wings of Liberty",
                    checked=State.expansion_wol,
                    on_change=State.set_expansion_wol,
                ),
                rx.checkbox(
                    text="Heart of the Swarm",
                    checked=State.expansion_hots,
                    on_change=State.set_expansion_hots,
                ),
                rx.checkbox(
                    text="Legacy of the Void",
                    checked=State.expansion_lotv,
                    on_change=State.set_expansion_lotv,
                ),
                style=[FIELDSET_SUB_STYLE],
            ),
            rx.el.fieldset(
                rx.el.legend("Regions"),
                rx.checkbox(
                    text="Americas",
                    checked=State.server_americas,
                    on_change=State.set_server_americas,
                ),
                rx.checkbox(
                    text="Europe",
                    checked=State.server_europe,
                    on_change=State.set_server_europe,
                ),
                rx.checkbox(
                    text="Asia",
                    checked=State.server_asia,
                    on_change=State.set_server_asia,
                ),
                style=[FIELDSET_SUB_STYLE],
            ),
            rx.el.fieldset(
                rx.el.legend("Date played"),
                rx.flex(
                    rx.text("Between"),
                    rx.input(
                        type="datetime-local",
                        value=State.date_played_min,
                        on_change=State.set_date_played_min,
                    ),
                    rx.text("and"),
                    rx.input(
                        type="datetime-local",
                        value=State.date_played_max,
                        on_change=State.set_date_played_max,
                    ),
                    spacing="2",
                    align="center",
                ),
                style=[FIELDSET_SUB_STYLE],
            ),
            rx.el.fieldset(
                rx.el.legend("Game duration"),
                rx.flex(
                    rx.text("Between"),
                    rx.input(
                        type="time",
                        value=State.game_duration_min,
                        on_change=State.set_game_duration_min,
                    ),
                    rx.text("and"),
                    rx.input(
                        type="time",
                        value=State.game_duration_max,
                        on_change=State.set_game_duration_max,
                    ),
                    spacing="2",
                    align="center",
                ),
                style=[FIELDSET_SUB_STYLE],
            ),
            rx.el.fieldset(
                rx.el.legend("Player count"),
                rx.flex(
                    rx.text("Between"),
                    rx.input(
                        type="number",
                        value=State.player_count_min,
                        on_change=State.set_player_count_min,
                    ),
                    rx.text("and"),
                    rx.input(
                        type="number",
                        value=State.player_count_max,
                        on_change=State.set_player_count_max,
                    ),
                    spacing="2",
                    align="center",
                ),
                style=[FIELDSET_SUB_STYLE],
            ),
            rx.el.fieldset(
                rx.el.legend("Average Player MMR"),
                rx.flex(
                    rx.text("Between"),
                    rx.input(
                        type="number",
                        value=State.average_mmr_min,
                        on_change=State.set_average_mmr_min,
                    ),
                    rx.text("and"),
                    rx.input(
                        type="number",
                        value=State.average_mmr_max,
                        on_change=State.set_average_mmr_max,
                    ),
                    spacing="2",
                    align="center",
                ),
                style=[FIELDSET_SUB_STYLE],
            ),
            rx.el.fieldset(
                rx.el.legend("Matchups"),
                rx.grid(
                    rx.checkbox(
                        text="PvP",
                        checked=State.matchup_pvp,
                        on_change=State.set_matchup_pvp,
                    ),
                    rx.checkbox(
                        text="PvT",
                        checked=State.matchup_pvt,
                        on_change=State.set_matchup_pvt,
                    ),
                    rx.checkbox(
                        text="PvZ",
                        checked=State.matchup_pvz,
                        on_change=State.set_matchup_pvz,
                    ),
                    rx.checkbox(
                        text="TvT",
                        checked=State.matchup_tvt,
                        on_change=State.set_matchup_tvt,
                    ),
                    rx.checkbox(
                        text="TvZ",
                        checked=State.matchup_tvz,
                        on_change=State.set_matchup_tvz,
                    ),
                    rx.checkbox(
                        text="ZvZ",
                        checked=State.matchup_zvz,
                        on_change=State.set_matchup_zvz,
                    ),
                    columns="3",
                    spacing="2",
                ),
                style=[FIELDSET_SUB_STYLE],
            ),
            rx.el.fieldset(
                rx.el.legend("Player name (partial match, case insensitive)"),
                rx.grid(
                    rx.text(
                        "Must include names",
                        style={"white-space": "nowrap"},
                    ),
                    rx.input(
                        value=State.player_name_must_include,
                        on_change=State.set_player_name_must_include,
                        style={"width": "100%", "grid-column": "span 2 / span 2"},
                    ),
                    rx.text(
                        "Must exclude names",
                        style={"white-space": "nowrap"},
                    ),
                    rx.input(
                        value=State.player_name_must_exclude,
                        on_change=State.set_player_name_must_exclude,
                        style={"width": "100%", "grid-column": "span 2 / span 2"},
                    ),
                    columns="3",
                    align="center",
                    spacing="2",
                ),
                style=[FIELDSET_SUB_STYLE],
            ),
            rx.el.fieldset(
                rx.el.legend("Map name (partial match, case insensitive)"),
                rx.grid(
                    rx.text(
                        "Must include names",
                        style={"white-space": "nowrap"},
                    ),
                    rx.input(
                        value=State.map_name_must_include,
                        on_change=State.set_map_name_must_include,
                        style={"width": "100%", "grid-column": "span 2 / span 2"},
                    ),
                    rx.text(
                        "Must exclude names",
                        style={"white-space": "nowrap"},
                    ),
                    rx.input(
                        value=State.map_name_must_exclude,
                        on_change=State.set_map_name_must_exclude,
                        style={"width": "100%", "grid-column": "span 2 / span 2"},
                    ),
                    columns="3",
                    align="center",
                    spacing="2",
                ),
                style=[FIELDSET_SUB_STYLE],
            ),
            direction="column",
            spacing="2",
        ),
        style=[FIELDSET_STYLE],
    )


def _name_template_component() -> rx.Component:
    # TODO Add tooltip
    return rx.el.fieldset(
        rx.el.legend("Name Template"),
        rx.grid(
            rx.text(
                "Custom Pattern",
                style={"white-space": "nowrap"},
            ),
            rx.input(
                value=State.replay_name_pattern,
                on_change=State.set_replay_name_pattern,
                style={"width": "100%", "grid-column": "span 2 / span 2"},
            ),
            rx.text(
                "Preview",
                style={"white-space": "nowrap"},
            ),
            rx.text(
                f"{State.replay_name_pattern}",
                style={"text-align": "left", "grid-column": "span 2 / span 2"},
            ),
            columns="3",
            align="center",
            spacing="2",
        ),
        style=[FIELDSET_STYLE],
    )


def _zip_and_download_button() -> rx.Component:
    # TODO Implement zip and download
    replays_processing_count = State.replays_processing_count
    replays_passing_filter_count = State.get_all_filtered_replays.length()

    # TODO Deactivate download button if there are replays processing, or if no replay passes the filter
    # rx.console_log(replays_passing_filter_count)
    # print(f"{replays_passing_filter_count2}")
    return rx.flex(
        rx.cond(
            0 < replays_processing_count,
            rx.text(f"Processing: {State.replays_processing_count}"),
            None,
        ),
        rx.button(
            rx.icon("download"),
            rx.cond(
                0 < replays_passing_filter_count,
                f"Zip and download {replays_passing_filter_count} replays",
                "Zip and download replays",
            ),
            on_click=State.zip_filtered_replays,  # pyright: ignore[reportArgumentType]
        ),
        direction="column",
        align="center",
    )


def index() -> rx.Component:
    return rx.flex(
        _upload_component(),
        _filter_component(),
        _name_template_component(),
        _zip_and_download_button(),
        direction="column",
        justify="center",
        align="center",
        spacing="2",
        style={"padding": "2.5rem", "min-height": "100vh"},
    )
