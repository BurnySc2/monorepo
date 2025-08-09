from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Annotated, Any, Literal

import sc2reader
from litestar import Controller, get, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.response import Template
from pydantic import BaseModel
from sc2reader.resources import Replay


@dataclass
class ReplayRequest:
    file: UploadFile


class ReplayPlayer(BaseModel):
    clan_tag: str  # Empty string if not in clan
    name: str
    pick_race: Literal["Random", "Protoss", "Terran", "Zerg"]
    play_race: Literal["Protoss", "Terran", "Zerg"]
    is_human: bool
    mmr: int | None  # Only visible in ranked match


class ReplayTeam(BaseModel):
    result: Literal["Win", "Loss"]
    players: list[ReplayPlayer]


class ReplayData(BaseModel):
    teams: list[ReplayTeam]
    played_timestamp: int
    game_length_seconds: int
    map_name: str
    region_short: Literal["us", "eu", "kr"]
    expansion: Literal["WoL", "HotS", "LotV"]
    game_base_build: int
    game_version: str
    game_type: str
    is_ladder: bool
    is_private: bool
    resume_from_replay: bool
    # chat_messages: list[ReplayMessage]


class MyReplayPackBuilderRoute(Controller):
    path = "/sc2-replay-pack-builder"

    @get("/")
    async def index(
        self,
    ) -> Template:
        return Template(
            template_name="replay_pack_builder/index.html",
            context={},
        )

    @post("/parse-replay")
    async def parse_replay(
        self,
        data: Annotated[ReplayRequest, Body(media_type=RequestEncodingType.MULTI_PART)],
    ) -> dict[str, Any]:
        bytes = BytesIO(data.file.file.read())
        # https://sc2reader.readthedocs.io/en/latest/articles/gettingstarted.html
        replay: Replay = sc2reader.load_replay(bytes, load_level=2)

        parsed = {
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
                        for player in team.players
                    ],
                }
                for team in replay.teams
            ],
            "is_ladder": replay.is_ladder,
            "is_private": replay.is_private,
            "resume_from_replay": replay.resume_from_replay,
            "game_length_seconds": replay.length.seconds,
            "game_base_build": replay.base_build,
            "game_version": ".".join(map(str, replay.versions[1:4])),
            "game_type": replay.type,
            "played_timestamp": replay.unix_timestamp,
            "map_name": replay.map_name,
            "region_short": replay.region,
            "expansion": replay.expansion,
        }
        parsed_checked = ReplayData(**parsed)
        return parsed_checked.model_dump()
