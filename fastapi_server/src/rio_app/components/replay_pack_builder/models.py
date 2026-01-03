from __future__ import annotations

from dataclasses import dataclass
from hashlib import md5
from typing import Literal

import arrow
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
    played_timestamp: float
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
        key = file_response["Key"]
        user_id, name = key.split("/")
        stem, _suffix = name.split(".")
        return ReplayFile(
            user_id=user_id,
            size=file_response["Size"],
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

    played_timestamp: float
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

    def rename_file_according_to_template(self, replay_name_pattern: str) -> str:
        class Player(BaseModel):
            name: str
            race: str
            mmr: int | None

        player1 = Player(name="", race=" ", mmr=None)
        player2 = Player(name="", race=" ", mmr=None)
        for i1, team in enumerate(self.teams):
            for _, player in enumerate(team.players):
                if i1 == 0:
                    player1 = Player(name=player.name, race=player.play_race, mmr=player.mmr or 0)
                elif i1 == 1:
                    player2 = Player(name=player.name, race=player.play_race, mmr=player.mmr or 0)

        datetime = arrow.get(self.played_timestamp)
        minutes, seconds = [self.game_length_seconds // 60, self.game_length_seconds % 60]
        placeholders = {
            "date": datetime.format("YYYY_MM_DD"),
            "time": datetime.format("hh_mm_ss"),
            "duration": f"{minutes}m {seconds:02d}s",
            "map": self.map_name.replace(" ", "_"),
            "region": self.region_short,
            "REGION": self.region_short.upper(),
            "version": self.game_version,
            "p1name": player1.name,
            "p1race": player1.race,
            "p1r": player1.race[0],
            "p1mmr": player1.mmr,
            "p2name": player2.name,
            "p2race": player2.race,
            "p2r": player2.race[0],
            "p2mmr": player2.mmr,
        }
        new_name = replay_name_pattern
        for placeholder, value in placeholders.items():
            new_name = new_name.replace(f"{{{placeholder}}}", f"{value}")
        return new_name
