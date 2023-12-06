"""Fetches build orders with certain conditions.
Searches aoe4 players.
Analyses games."""
from __future__ import annotations

import asyncio
import enum
import re
from dataclasses import dataclass
from typing import List, Optional, Union

import aiohttp
import arrow
from aiohttp import ClientSession, TCPConnector
from hikari import GatewayBot, GuildMessageCreateEvent
from loguru import logger
from pydantic import BaseModel, Field, validator
from simple_parsing import ArgumentParser, field

TCP_CONNECTOR_LIMIT = 10

# START OF ARGPARSER
ALLOWED_RACES = {"ab", "ch", "de", "en", "fr", "ho", "ma", "mo", "ot", "ru"}


class Operator(enum.Enum):
    UNKNOWN = 0
    HAS = 1
    BEFORE = 2


class Action(enum.Enum):
    UNKNOWN = 0
    VILLAGER = 1
    TOWNCENTER = 2
    FEUDAL = 3
    CASTLE = 4
    IMPERIAL = 5
    WHEELBARROW = 6

    @staticmethod
    def parse_action(action: str) -> Action:
        action = action.lower()
        if action in {"v", "villager", "villagers"}:
            return Action.VILLAGER
        if action in {"tc", "tcs", "towncenter", "towncenters"}:
            return Action.TOWNCENTER
        if action in {"age2", "feudal"}:
            return Action.FEUDAL
        if action in {"age3", "castle"}:
            return Action.CASTLE
        if action in {"age4", "imp", "imperial"}:
            return Action.IMPERIAL
        if action in {"wb", "wheel", "wheelbarrow"}:
            return Action.WHEELBARROW
        raise ValueError(f"Doesn't exist: {action}")


# pyre-fixme[13]
class Condition(BaseModel):
    action: Action
    target_count: int
    operator: Operator
    time_in_seconds: Optional[int] = None

    @staticmethod
    def from_string(condition: str) -> Condition:
        """Needs to be able to parse:

        4 town centers before 10 minutes:
            4towncenters<600
            4towncenters<600s
            4towncenters<10m
        wheelbarrow researched:
            1wheelbarrow
            wheelbarrow
        target 60 villager count before time 600
            60villagers<600s
        """
        default_count = 1
        operator = Operator.UNKNOWN

        optional_count_regex = r"(\d+)?"
        action_regex = r"(\w+)"
        operator_regex = "(<)?"
        time_regex = r"(\d+)?"
        time_suffix_regex = "(s|m)?"
        matcher_regex = f"{optional_count_regex}{action_regex}{operator_regex}{time_regex}{time_suffix_regex}"
        compiled = re.compile(matcher_regex)
        regex_match = compiled.fullmatch(condition)

        if regex_match is None:
            raise ValueError("Unable to parse condition.")

        count = default_count if regex_match.group(1) is None else int(regex_match.group(1))
        action_string = regex_match.group(2)
        operator_parsed = regex_match.group(3)
        if operator_parsed is not None and operator_parsed == "<":
            operator = Operator.BEFORE

        duration = None if regex_match.group(4) is None else int(regex_match.group(4))
        time_suffix = regex_match.group(5)
        if duration is not None and time_suffix is not None and time_suffix == "m":
            duration *= 60

        return Condition(
            action=Action.parse_action(action_string),
            target_count=count,
            operator=operator,
            time_in_seconds=duration,
        )

    @property
    def to_string(self) -> str:
        seconds = self.time_in_seconds or ""
        operator = "<" if seconds else ""
        return f"{self.target_count}{self.action.name.lower()}{operator}{seconds}"


@dataclass
class BuildOrderParserOptions:
    # How many profiles to browse (1 to 100)
    profiles_limit: int = 50
    # How many games to browse per profile (1 to 100)
    games_per_profile: int = 50
    # If given a profile_id, will only check this profile for matches with the given build order conditions
    profile_id: int | None = field(alias=["-p", "-id"], default=None)
    # Only allow players to have played this civilization
    # One of: "ab", "ch", "de", "en", "fr", "ho", "ma", "mo", "ot", "ru"
    race: str = field(alias=["-r", "--civ", "--civilization"], default="en")
    # A list of conditions, e.g. "2tc<360s" or "wheelbarrow<240,feudal<360s,castle<11m"
    condition: str | None = field(alias=["-c", "--count"], default=None)

    # constant_villager_production: bool = field(alias=['-cvp'], default=False, action='store_true')

    def __post_init__(self):
        assert 1 <= self.profiles_limit <= 100
        assert 1 <= self.games_per_profile <= 100
        assert self.race.lower()[:2] in ALLOWED_RACES
        # TODO Check if conditions are valid? e.g. no imperial before castle

    @property
    def to_string(self) -> str:
        args = (
            [f"--profiles_limit {self.profiles_limit} --games_per_profile {self.games_per_profile} --race {self.race}"]
            # Optional profile_id
            + (["--profile_id", str(self.profile_id)] if self.profile_id is not None else [])
            # Optional condition
            + (["--condition", self.condition] if self.condition is not None else [])
        )
        return " ".join(args)

    @property
    def race_parsed(self) -> str:
        race = self.race.lower()[:2]
        if race in ALLOWED_RACES:
            return race
        raise ValueError

    @property
    def conditions_parsed(self) -> list[Condition]:
        if self.condition is None:
            return []
        return [Condition.from_string(c) for c in self.condition.split(",")]


public_fetch_aoe4_bo_parser = ArgumentParser()
public_fetch_aoe4_bo_parser.add_arguments(BuildOrderParserOptions, dest="params")  # pyre-fixme[6]


def get_help_string() -> str:
    _temp = public_fetch_aoe4_bo_parser.parse_known_args([])
    temp_help_string = public_fetch_aoe4_bo_parser.format_help()
    index_string = "BuildOrderParserOptions ['params']:"
    return temp_help_string[temp_help_string.find(index_string) + len(index_string):].strip()


help_string = get_help_string()


# END OF ARGPARSER
async def public_search_aoe4_players(
    bot: GatewayBot,
    event: GuildMessageCreateEvent,
    message: str,
):
    """Given a name, the bot will attempt to find matching profiles."""
    message = message.strip()
    async with aiohttp.ClientSession(
        connector=TCPConnector(
            # Limit amount of connections this ClientSession should posses
            limit=TCP_CONNECTOR_LIMIT,
            # Limit amount of connections per host
            limit_per_host=TCP_CONNECTOR_LIMIT,
        ),
    ) as session:
        logger.info(f"Searching for player name '{message}'")
        players: list[PlayerSearchResult] = await search(session, message)
        if len(players) == 0:
            return "Could not find any player with this name."
        players.sort(key=lambda player: player.last_game_at_arrow, reverse=True)
        players_string = "\n".join(
            [
                f"Last game was {player.last_game_at_arrow.humanize()}, {player.name} "
                f"<https://aoe4world.com/players/{player.profile_id}>"
                # Only list the first 10 players
                for player in players[:10]
            ]
        )
        return players_string


async def public_analyse_aoe4_game(
    bot: GatewayBot,
    event: GuildMessageCreateEvent,
    message: str,
) -> str:
    '''Needs to be able to parse
    message = "https://aoe4world.com/players/7344587/games/65673113"
    message = "<https://aoe4world.com/players/7344587/games/65673113>"
    then analyzes the games and gives information about the macro of the player.
    '''
    message = message.strip("<").strip(">")
    game_url_pattern = r"https://aoe4world\.com/players/(\d+).*/games/(\d+).*"
    game_url_compiled = re.compile(game_url_pattern)
    match = game_url_compiled.fullmatch(message)
    if match is None:
        return (
            "Unable to process request. Please submit a link to a match, e.g. "
            "<https://aoe4world.com/players/7344587/games/65673113>"
        )

    player_profile_id = int(match.group(1))
    game_id = int(match.group(2))

    async with aiohttp.ClientSession(
        connector=TCPConnector(
            # Limit amount of connections this ClientSession should posses
            limit=TCP_CONNECTOR_LIMIT,
            # Limit amount of connections per host
            limit_per_host=TCP_CONNECTOR_LIMIT,
        ),
    ) as session:
        data: tuple[GamePlayerData, int, int] | None = await get_build_order_of_game(
            session,
            game_id,
            player_profile_id,
        )
        if data is None:
            return "Game was not found. Is the link valid?"
        game_player_data: GamePlayerData = data[0]
        url = f"https://aoe4world.com/players/{player_profile_id}/games/{game_id}"
        return f"Analysis of game <{url}>\n{game_player_data.to_discord_message()}"


async def public_fetch_aoe4_bo(
    bot: GatewayBot,
    event: GuildMessageCreateEvent,
    message: str,
) -> str:
    """Using arg parser as helper, allow multiple arguments and then send multiple requests to the aoe4world API.
    Grab build orders and match them against certain conditions."""
    unknown_args: list[str]
    try:
        parsed, unknown_args = public_fetch_aoe4_bo_parser.parse_known_args(args=message.split())
    except SystemExit:
        return help_string
    if len(unknown_args) > 0:
        return help_string
    parsed_params: BuildOrderParserOptions = parsed.params
    collected_games: list[CollectedBuildOrder] = []
    parsed_games_count = 0
    parsed_build_orders_count = 0
    logger.debug("Fetching...")
    async with aiohttp.ClientSession(
        connector=TCPConnector(
            # Limit amount of connections this ClientSession should posses
            limit=TCP_CONNECTOR_LIMIT,
            # Limit amount of connections per host
            limit_per_host=TCP_CONNECTOR_LIMIT,
        ),
    ) as session:
        map_profile_id_to_player_profile: dict[int, PlayerSearchResult] = {}
        get_games_by_player_tasks = []
        if parsed_params.profile_id is not None:
            # A single profile id was given
            profile_response = await session.get(f"https://aoe4world.com/api/v0/players/{parsed_params.profile_id}")
            if not profile_response.ok:
                return "Could not find a profile with this id."
            data = await profile_response.json()
            profiles = [PlayerSearchResult.parse_obj(data)]
        else:
            profiles = await fetch_top_profiles(
                session,
                max_pages=max(1, parsed_params.profiles_limit // 50),
            )
        for profile in profiles:
            map_profile_id_to_player_profile[profile.profile_id] = profile

            pages_to_browse = max(1, parsed_params.games_per_profile // 50)
            if parsed_params.profile_id is not None:
                # Parse all pages because only one profile was given
                pages_to_browse = 20

            get_games_by_player_tasks.append(
                asyncio.create_task(
                    get_games_by_player_id(
                        session,
                        player_profile_id=profile.profile_id,
                        allowed_race=parsed_params.race,
                        max_pages=pages_to_browse,
                    )
                )
            )
        logger.debug(f"Found {len(get_games_by_player_tasks)} profiles")

        map_game_id_to_game_result: dict[int, GameResult] = {}
        get_build_order_tasks = []
        # Iterate them in any order
        for future in asyncio.as_completed(get_games_by_player_tasks):
            for (game_result, player_profile_id) in await future:
                game_result: GameResult
                map_game_id_to_game_result[game_result.game_id] = game_result
                get_build_order_tasks.append(
                    asyncio.create_task(
                        get_build_order_of_game(
                            session,
                            game_id=game_result.game_id,
                            player_profile_id=player_profile_id,
                        )
                    )
                )
                parsed_games_count += 1
        logger.debug(f"{parsed_games_count=}")

        latest_patch = 0
        # Iterate them in any order
        for future in asyncio.as_completed(get_build_order_tasks):
            data: tuple[GamePlayerData, int, int] | None = await future
            if data is None:
                continue
            game_player_data, game_id, player_profile_id = data
            parsed_build_orders_count += 1

            # Only collect games from latest patch
            if game_result.patch > latest_patch:
                latest_patch = game_result.patch
                collected_games.clear()

            if not game_player_data.matches_all_conditions(parsed_params.conditions_parsed):
                continue
            # Build order survived condition filters
            collected_games.append(
                CollectedBuildOrder(
                    game_result=map_game_id_to_game_result[game_id],
                    game_player_data=game_player_data,
                    player_profile=map_profile_id_to_player_profile[player_profile_id],
                )
            )
            logger.debug(f"Games matching the filter: {len(collected_games)}")
        logger.debug(f"{parsed_build_orders_count=}")

    if len(collected_games) == 0:
        return f"Parsed {parsed_games_count} games. No games match this request"
    collected_games.sort(key=lambda item: item.arrow_played_at, reverse=True)
    collected_games_string = "\n".join(map(str, collected_games[:10]))
    return f"""Found {len(collected_games)} games that match this request
{collected_games_string}"""


# pyre-fixme[13]
class Social(BaseModel):
    twitch: Optional[str]
    twitter: Optional[str]
    instagram: Optional[str]
    liquipedia: Optional[str]


# pyre-fixme[13]
class Leaderboard(BaseModel):
    rating: int
    max_rating: Optional[int]
    max_rating_7d: Optional[int]
    max_rating_1m: Optional[int]
    rank: Optional[int]
    rank_level: Optional[str] = None
    streak: int
    games_count: int
    wins_count: int
    losses_count: int
    last_game_at: str
    win_rate: float

    @property
    def last_game_at_arrow(self) -> arrow.Arrow:
        return arrow.get(self.last_game_at)


class Leaderboards(BaseModel):
    rm_team: Optional[Leaderboard] = None
    rm_1v1_elo: Optional[Leaderboard] = None
    rm_2v2_elo: Optional[Leaderboard] = None
    rm_3v3_elo: Optional[Leaderboard] = None
    rm_4v4_elo: Optional[Leaderboard] = None


# pyre-fixme[13]
class PlayerSearchResult(BaseModel):
    name: str
    profile_id: int
    steam_id: str
    country: Optional[str] = None
    social: Social
    last_game_at: Optional[str]
    leaderboards: Optional[Leaderboards]

    @property
    def last_game_at_arrow(self) -> arrow.Arrow:
        if self.last_game_at is None:
            return arrow.utcnow().shift(years=-1)
        return arrow.get(self.last_game_at)


# pyre-fixme[13]
class PlayerOfTeam(BaseModel):
    profile_id: Optional[int]
    name: Optional[str]
    result: Optional[str]
    civilization: str
    civilization_randomized: Optional[bool]
    rating: Optional[int]
    rating_diff: Optional[int]


# pyre-fixme[13]
class PlayerOfTeamEntry(BaseModel):
    player: PlayerOfTeam


# pyre-fixme[13]
class GameResult(BaseModel):
    game_id: int
    started_at: str
    updated_at: str
    duration: Optional[int]
    map: str
    kind: str
    leaderboard: str
    season: int
    server: str
    patch: int
    average_rating: Optional[int]
    ongoing: bool
    just_finished: bool
    teams: List[List[PlayerOfTeamEntry]]


class FinishedActions(BaseModel):
    feudal_age: List[int] = Field(default_factory=list)
    castle_age: List[int] = Field(default_factory=list)
    imperial_age: List[int] = Field(default_factory=list)
    upgrade_unit_town_center_wheelbarrow_1: List[int] = Field(default_factory=list)
    # TODO More upgrades


# pyre-fixme[13]
class BuildOrderItem(BaseModel):
    id: Optional[Union[str, int]]
    icon: str
    type: str
    finished: List[int]
    constructed: List[int]
    packed: List[int]
    unpacked: List[int]
    transformed: List[int]
    destroyed: List[int]

    @validator("id", check_fields=False)
    def format_id(cls, v: str | int | None) -> int | None:
        if v is None:
            return None
        if isinstance(v, int):
            return v
        v = v.strip()
        if not v.isnumeric():
            # id has weird signs in them
            digits_collected = []
            for digit in v:
                if digit.isnumeric():
                    digits_collected.append(digit)
            new_id = "".join(digits_collected)
            if new_id == "":
                return None
            return int(new_id)
        return int(v)


def format_time(timestamps: list[int]) -> str:
    '''From a given list of timestamps, convert them to minute:second format
    E.g. input is [30, 90], output will be "0:30, 1:30"
    '''
    times_formatted: list[str] = []
    for timestamp in timestamps:
        minutes, seconds = divmod(timestamp, 60)
        times_formatted.append(f"{minutes}:{seconds:02}")
    return ", ".join(times_formatted)


# pyre-fixme[13]
class GamePlayerData(BaseModel):
    profile_id: Optional[int]
    name: Optional[str]
    civilization: str
    team: int
    apm: Optional[int]
    actions: FinishedActions
    build_order: List[BuildOrderItem]

    def finished_list_of_icon(self, icon_name: str) -> list[int]:
        for item in self.build_order:
            if item.icon == icon_name:
                assert len(item.finished) == 0 or len(item.constructed) == 0
                # .finished is filled for units and upgrades, and .constructed is filled for buildings
                return item.finished + item.constructed
        raise IndexError(f"Could not find icon in build order: {icon_name}")

    def check_condition(self, condition: Condition) -> bool:
        """ Returns true if this build order matches the given condition. """
        # VILLAGER CONDITION
        if condition.action == Action.VILLAGER:
            if condition.time_in_seconds is None:
                raise ValueError("Time for villager count must not be 'None'.")
            finished_list = self.finished_list_of_icon("icons/races/common/units/villager")
            if condition.time_in_seconds is None:
                bo_count = len(finished_list)
            else:
                # pyre-fixme[58]
                bo_count = sum(1 for i in finished_list if i <= condition.time_in_seconds)
            return bo_count >= condition.target_count
        # TOWNCENTER CONDITION
        if condition.action == Action.TOWNCENTER:
            if condition.time_in_seconds is None:
                raise ValueError("Time for villager count must not be 'None'.")
            finished_list = self.finished_list_of_icon("icons/races/common/buildings/town_center")
            if condition.time_in_seconds is None:
                bo_count = len(finished_list)
            else:
                # pyre-fixme[58]
                bo_count = sum(1 for i in finished_list if i <= condition.time_in_seconds)
            return bo_count >= condition.target_count
        # FEUDAL CONDITION
        if condition.action == Action.FEUDAL:
            if len(self.actions.feudal_age) == 0:
                return False
            if condition.time_in_seconds is None:
                return True
            if len(self.actions.feudal_age) > 0:
                # pyre-fixme[58]
                return self.actions.feudal_age[0] <= condition.time_in_seconds
            return False
        # CASTLE CONDITION
        if condition.action == Action.CASTLE:
            if len(self.actions.castle_age) == 0:
                return False
            if condition.time_in_seconds is None:
                return True
            if len(self.actions.castle_age) > 0:
                # pyre-fixme[58]
                return self.actions.castle_age[0] <= condition.time_in_seconds
            return False
        # IMPERIAL CONDITION
        if condition.action == Action.IMPERIAL:
            if len(self.actions.imperial_age) == 0:
                return False
            if condition.time_in_seconds is None:
                return True
            if len(self.actions.imperial_age) > 0:
                # pyre-fixme[58]
                return self.actions.imperial_age[0] <= condition.time_in_seconds
            return False
        # WHEELBARROW CONDITION
        if condition.action == Action.WHEELBARROW:
            if len(self.actions.upgrade_unit_town_center_wheelbarrow_1) == 0:
                return False
            if condition.time_in_seconds is None:
                return True
            if len(self.actions.upgrade_unit_town_center_wheelbarrow_1) > 0:
                # pyre-fixme[58]
                return self.actions.upgrade_unit_town_center_wheelbarrow_1[0] <= condition.time_in_seconds
            return False
        raise NotImplementedError(f"Not implemented for action: {condition.action}")

    def matches_all_conditions(self, conditions: list[Condition]) -> bool:
        return all(self.check_condition(condition) for condition in conditions)

    def to_discord_message_towncenters(self) -> str:
        for item in self.build_order:
            if item.icon == "icons/races/common/buildings/town_center":
                if len(item.constructed) <= 1:
                    return ""
                return f"TCs completed: {format_time(item.constructed[1:])}"
        return ""

    def to_discord_message_villagers(self) -> str:
        count_timestamps_in_minutes = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        villager_counts: list[str] = []
        last_count = 0
        for item in self.build_order:
            if item.icon == "icons/races/common/units/villager":
                for max_timestamp in count_timestamps_in_minutes:
                    count = sum(1 for i in item.finished if i < max_timestamp * 60)
                    if count == last_count:
                        # Count didn't change, so game ended before?
                        break
                    last_count = count
                    villager_counts.append(f"{count} ({max_timestamp}m)")
                break
        if len(villager_counts) == 0:
            return ""
        return f"Villagers count: {', '.join(villager_counts)}"

    def to_discord_message_feudal(self) -> str:
        if len(self.actions.feudal_age) == 0:
            return ""
        return f"Feudal reached: {format_time(self.actions.feudal_age)}"

    def to_discord_message_castle(self) -> str:
        if len(self.actions.castle_age) == 0:
            return ""
        return f"Castle reached: {format_time(self.actions.castle_age)}"

    def to_discord_message_imperial(self) -> str:
        if len(self.actions.imperial_age) == 0:
            return ""
        return f"Imperial reached: {format_time(self.actions.imperial_age)}"

    def to_discord_message_wheelbarrow(self) -> str:
        if len(self.actions.upgrade_unit_town_center_wheelbarrow_1) == 0:
            return ""
        return f"Wheelbarrow researched: {format_time(self.actions.upgrade_unit_town_center_wheelbarrow_1)}"

    def to_discord_message(self) -> str:
        data = [
            self.to_discord_message_wheelbarrow(),
            self.to_discord_message_towncenters(),
            self.to_discord_message_feudal(),
            self.to_discord_message_castle(),
            self.to_discord_message_imperial(),
            self.to_discord_message_villagers(),
        ]
        info_string = "\n".join(i for i in data if i.strip() != "")
        return info_string


# pyre-fixme[13]
class CollectedBuildOrder(BaseModel):
    game_result: GameResult
    game_player_data: GamePlayerData
    player_profile: PlayerSearchResult

    @property
    def arrow_played_at(self) -> arrow.Arrow:
        return arrow.get(self.game_result.started_at)

    def __str__(self) -> str:
        time_ago = self.arrow_played_at.strftime("%Y-%m-%d %H:%M:%S")
        url = f"https://aoe4world.com/players/{self.game_player_data.profile_id}/games/{self.game_result.game_id}"
        return f"{time_ago} '{self.game_player_data.civilization[:2]}' {self.game_player_data.name} <{url}>"


async def search(
    session: aiohttp.ClientSession,
    player_name: str,
) -> list[PlayerSearchResult]:
    """A helper function to search for profiles via a player name query."""
    url = f"https://aoe4world.com/api/v0/players/search?query={player_name}"
    collected_players: list[PlayerSearchResult] = []
    response: aiohttp.ClientResponse
    response = await session.get(url)
    if not response.ok:
        raise aiohttp.ClientConnectionError
    data = await response.json()
    for player_data in data["players"]:
        player: PlayerSearchResult = PlayerSearchResult.parse_obj(player_data)
        collected_players.append(player)
    return collected_players


async def fetch_top_profiles(session: ClientSession, max_pages: int = 1) -> list[PlayerSearchResult]:
    """From the first n pages, grab the profiles and return them as generator."""
    assert max_pages >= 1
    tasks = [
        asyncio.create_task(session.get(f"https://aoe4world.com/api/v0/leaderboards/rm_solo?page={page}"))
        for page in range(1, max_pages + 1)
    ]
    collected_profiles: list[PlayerSearchResult] = []
    # Iterate them in any order
    for future in asyncio.as_completed(tasks):
        response: aiohttp.ClientResponse = await future
        if not response.ok:
            continue
        data = await response.json()
        for player_profle in data["players"]:
            profile = PlayerSearchResult.parse_obj(player_profle)
            collected_profiles.append(profile)
    return collected_profiles


async def get_games_by_player_id(
    session: aiohttp.ClientSession,
    player_profile_id: int,
    allowed_race: str | None,
    max_pages: int = 1,
) -> list[tuple[GameResult, int]]:
    """A helper function that finds the latest games from match history by this player.
    Optional filter: race.
    """
    assert max_pages >= 1
    tasks = [
        asyncio.create_task(
            session.get(f"https://aoe4world.com/api/v0/games?page={page}&profile_ids={player_profile_id}")
        ) for page in range(1, max_pages + 1)
    ]
    collected: list[tuple[GameResult, int]] = []
    # Iterate them in any order
    for future in asyncio.as_completed(tasks):
        response: aiohttp.ClientResponse = await future
        if not response.ok:
            continue
        data = await response.json()
        if not data["games"]:
            logger.debug("Exiting because there are no games in this request.")
            continue
        for game_data in data["games"]:
            game_result = GameResult.parse_obj(game_data)
            # Skip short games
            if game_result.ongoing or game_result.duration is None or game_result.duration <= 600:
                continue
            # If any player matches the allowed race, filter matches on this game
            for team in game_result.teams:
                for player_of_team_entry in team:
                    player = player_of_team_entry.player
                    if allowed_race is not None and player.civilization[:2] != allowed_race[:2]:
                        continue
                    # Ignore if profile_id is None
                    if player.profile_id is None:
                        continue
                    # Ignore if given profile is not of the player we are looking for
                    if player.profile_id != player_profile_id:
                        continue
                    collected.append((game_result, player_profile_id))
    return collected


async def get_build_order_of_game(
    session: aiohttp.ClientSession,
    game_id: int,
    player_profile_id: int,
) -> tuple[GamePlayerData, int, int] | None:
    """A helper function that gets and parses the build order from a game belonging to a player."""
    url = f"https://aoe4world.com/players/{player_profile_id}/games/{game_id}/summary"
    response = await session.get(url)
    if not response.ok:
        return
    data = await response.json()
    for player_data in data["players"]:
        parsed = GamePlayerData.parse_obj(player_data)
        if parsed.profile_id is None or player_profile_id != parsed.profile_id:
            # Not the player we are looking for
            continue
        # TODO Parse _stats, scores, resources?
        return parsed, game_id, player_profile_id


async def main():
    # Test argument parser

    # Search for player name and return list of players and profiles
    player_search_query = "burny"
    data = await public_search_aoe4_players(None, None, player_search_query)
    print(data)

    # Analyze game: give information about feudal, tc, wheelbarrow, villagers timestamps
    message = "<https://aoe4world.com/players/585764/games/66434421>"
    data = await public_analyse_aoe4_game(None, None, message)
    print(data)

    # message = "--profile_id 6672615 --race english --condition castle<720s"
    message = "--race english --condition 2towncenter<400s,wheelbarrow<900s,feudal<360s,castle<660s"
    # message = "--race english --profiles_limit 100 --games_per_profile 100 --condition castle<540s"
    data = await public_fetch_aoe4_bo(None, None, message)
    print(data)


if __name__ == "__main__":
    asyncio.run(main())
