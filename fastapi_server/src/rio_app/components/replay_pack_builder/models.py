# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportAttributeAccessIssue=false, reportImplicitOverride=false
from dataclasses import dataclass
from hashlib import md5
from typing import Literal

from pydantic import BaseModel


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
