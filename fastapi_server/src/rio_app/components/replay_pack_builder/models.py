from __future__ import annotations
from dataclasses import dataclass
from hashlib import md5
from typing import Literal

from pydantic import BaseModel
from rio import FileInfo
from types_aiobotocore_s3.type_defs import ObjectTypeDef


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
    user_id: str
    size: int
    md5: str
    status: Literal["uploaded", "processing", "processed", "error"] = "uploaded"

    @property
    def minio_key(self):
        return f"{self.user_id}/{self.md5}.SC2Replay"

    @classmethod
    def from_minio(cls, file_response: ObjectTypeDef) -> ReplayFile:
        key = file_response["Key"]  # pyright: ignore[reportTypedDictNotRequiredAccess]
        user_id, name = key.split("/")
        stem, _suffix = name.split(".")
        return ReplayFile(
            user_id=user_id,
            size=file_response["Size"],  # pyright: ignore[reportTypedDictNotRequiredAccess]
            md5=stem,
            status="uploaded",
        )

    @classmethod
    def from_file_info(cls, user_id: str, file_info: FileInfo, data: bytes) -> ReplayFile:
        return ReplayFile(
            user_id=user_id,
            size=file_info.size_in_bytes,
            md5=cls.calculate_md5(data),
            status="uploaded",
        )

    @classmethod
    def calculate_md5(cls, data: bytes) -> str:
        return md5(data).hexdigest()


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
