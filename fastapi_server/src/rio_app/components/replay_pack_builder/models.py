# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportAttributeAccessIssue=false, reportImplicitOverride=false
from dataclasses import dataclass
from hashlib import md5
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from rio import FileInfo

REPLAYS_FOLDER = Path(__file__).parents[4] / "data" / "replay_pack_builder"
REPLAYS_FOLDER.mkdir(parents=True, exist_ok=True)


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
    path: Path | None = None
    size: int
    md5: str
    status: Literal["uploaded", "processing", "processed", "error"] = "uploaded"

    @classmethod
    def from_file(cls, file: Path) -> "ReplayFile":
        return ReplayFile(
            path=file,
            size=file.stat().st_size,
            md5=file.stem,
            status="uploaded",
        )

    @classmethod
    def from_file_info(cls, file_info: FileInfo, data: bytes) -> "ReplayFile":
        return ReplayFile(
            size=file_info.size_in_bytes,
            md5=cls.calculate_md5(data),
            status="uploaded",
        )

    @classmethod
    def calculate_md5(cls, data: bytes) -> str:
        return md5(data).hexdigest()

    def save_to_disk(self, user_id: str, data: bytes) -> int:
        temp_replay_path = REPLAYS_FOLDER / f"{self.md5}.uploading"
        replay_path = REPLAYS_FOLDER / user_id / f"{self.md5}.SC2Replay"
        replay_path.parent.mkdir(parents=True, exist_ok=True)
        _ = temp_replay_path.write_bytes(data)
        _ = temp_replay_path.rename(replay_path)
        self.path = replay_path
        return self.size

    def read_file(self) -> bytes:
        assert self.path is not None
        return self.path.read_bytes()


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
