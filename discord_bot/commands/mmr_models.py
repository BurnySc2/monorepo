from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Stats(BaseModel):
    rating: Optional[int] = None
    games_played: Optional[int] = Field(..., alias="gamesPlayed")
    rank: Optional[int] = None


class Partition(Enum):
    GLOBAL = "GLOBAL"


class Account(BaseModel):
    battle_tag: str = Field(..., alias="battleTag")
    id: int
    partition: Partition
    hidden: None


class Region(Enum):
    EU = "EU"
    KR = "KR"
    US = "US"


class Character(BaseModel):
    realm: int
    name: str
    id: int
    account_id: int = Field(..., alias="accountId")
    region: Region
    battlenet_id: int = Field(..., alias="battlenetId")


class Clan(BaseModel):
    tag: str
    id: int
    region: Region
    name: Optional[str]
    members: Optional[int]
    active_members: Optional[int] = Field(..., alias="activeMembers")
    avg_rating: Optional[int] = Field(..., alias="avgRating")
    avg_league_type: Optional[int] = Field(..., alias="avgLeagueType")
    games: Optional[int]


class Members(BaseModel):
    character: Character
    account: Account
    zerg_games_played: int = Field(0, alias="zergGamesPlayed")
    terran_games_played: int = Field(0, alias="terranGamesPlayed")
    clan: Optional[Clan] = None
    protoss_games_played: int = Field(0, alias="protossGamesPlayed")
    random_games_played: int = Field(0, alias="randomGamesPlayed")


class PlayerData(BaseModel):
    league_max: int = Field(..., alias="leagueMax")
    rating_max: int = Field(..., alias="ratingMax")
    total_games_played: int = Field(..., alias="totalGamesPlayed")
    previous_stats: Stats = Field(..., alias="previousStats")
    current_stats: Stats = Field(..., alias="currentStats")
    members: Members
