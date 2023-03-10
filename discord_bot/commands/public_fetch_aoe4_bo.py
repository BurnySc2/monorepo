from __future__ import annotations

import asyncio
import enum
import math
import re
from dataclasses import dataclass
from string import digits
from typing import AsyncGenerator

import aiohttp
import arrow
from hikari import GatewayBot, GuildMessageCreateEvent
from pydantic import BaseModel, validator, Field
from simple_parsing import ArgumentParser, field
""" START OF ARGPARSER """
# TODO Argparser should allow:
# !findbo --race english --towncenter <500s --wheelbarrow <300s --castle <700s --constant_villager_production

ALLOWED_RACES = {
    "en",
    # TODO all other races
}


class Operator(enum.Enum):
    UNKNOWN = 0
    HAS = 1
    BEFORE = 2
    # AFTER = 3


class Action(enum.Enum):
    UNKNOWN = 0
    VILLAGER = 1
    TOWNCENTER = 2
    FEUDAL = 3
    CASTLE = 4
    # IMPERIAL = 5
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
        # if action in {"age4", "imp", "imperial"}:
        #     return Action.IMPERIAL
        if action in {"wb", "wheelbarrow"}:
            return Action.WHEELBARROW
        raise ValueError(f"Doesn't exist: {action}")


class Condition(BaseModel):
    action: Action
    target_count: int
    operator: Operator | None = None
    time_in_seconds: int | None = None

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
        operator = Operator.HAS

        optional_count_regex = "(\d+)?"
        action_regex = "(\w+)"
        operator_regex = "(<)?"
        time_regex = "(\d+)?"
        time_suffix_regex = "(s|m)?"
        matcher_regex = f"{optional_count_regex}{action_regex}{operator_regex}{time_regex}{time_suffix_regex}"
        compiled = re.compile(matcher_regex)
        regex_match = compiled.fullmatch(condition)

        count = default_count if regex_match.group(1) is None else int(regex_match.group(1))
        action_string = regex_match.group(2)
        operator_parsed = regex_match.group(3)
        if operator_parsed is not None and operator_parsed == "<":
            operator = Operator.BEFORE

        duration = int(regex_match.group(4))
        time_suffix = regex_match.group(5)
        if time_suffix is not None and time_suffix == "m":
            duration *= 60

        return Condition(
            action=Action.parse_action(action_string),
            target_count=count,
            operator=operator,
            time_in_seconds=duration,
        )


@dataclass
class BuildOrderParserOptions:
    min_rating: int | None = field(alias=['-m'], default=None)
    max_rating: int | None = field(default=None)
    profile_id: int | None = field(alias=['-p', '-id'], default=None)
    race: str = field(alias=["-r"], default="en")
    # constant_villager_production: bool = field(alias=['-cvp'], default=False, action='store_true')
    condition: str | None = field(alias=["-c", "--count"], default=None)

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
public_fetch_aoe4_bo_parser.add_arguments(BuildOrderParserOptions, dest='params')
""" END OF ARGPARSER """


async def public_search_aoe4_players(
    bot: GatewayBot,
    event: GuildMessageCreateEvent,
    message: str,
):
    message = message.strip()
    # TODO query: playername, return profile_ids associated with player name (return link)
    async with aiohttp.ClientSession() as session:
        print(f"Searching for player name '{message}'")
        async for player in search(session, message):
            print(f"{player.profile_id} {player.name} <https://aoe4world.com/players/{player.profile_id}>")
    # TODO Collect players from this print string, then return


async def public_fetch_aoe4_bo(
    bot: GatewayBot,
    event: GuildMessageCreateEvent,
    message: str,
):
    message = message.strip()

    unknown_args: list[str]
    try:
        parsed, unknown_args = public_fetch_aoe4_bo_parser.parse_known_args(args=message.split())
        # a = parsed.params.conditions_parsed
    except SystemExit:
        return

    # Sanity checks
    if parsed.params.min_rating is not None and parsed.params.max_rating is not None:
        assert parsed.params.min_rating <= parsed.params.max_rating

    parsed_games_count = 0
    collected_games: list[str] = []
    async with aiohttp.ClientSession() as session:
        # Fetch games by player profile_id and race
        if parsed.params.profile_id is not None:
            profile_id: int = parsed.params.profile_id
            async for game in get_games_by_player_id(session, profile_id, allowed_race=parsed.params.race):
                print(game)
                await get_build_order_of_game(session, game.game_id, profile_id)
            # TODO Fetch games where filter works
            return
        # Fetch all games by rating and race
        else:
            game_result: GameResult
            game_player_data: GamePlayerData
            async for (game_result, game_player_data) in get_all_games(
                session,
                min_rating=parsed.params.min_rating,
                max_rating=parsed.params.max_rating,
                allowed_race=parsed.params.race,
            ):
                # Dont browse further than X days
                time_ago: arrow.Arrow = arrow.utcnow().shift(days=-14)
                game_started_time: arrow.Arrow = arrow.get(game_result.started_at)
                if game_started_time < time_ago:
                    break
                parsed_games_count += 1

                conditions_met = True
                condition: Condition
                for condition in parsed.params.conditions_parsed:
                    if not game_player_data.check_condition(condition):
                        conditions_met = False
                        break
                if not conditions_met:
                    continue
                # Build order survived condition filters
                url = f"https://aoe4world.com/players/{game_player_data.profile_id}/games/{game_result.game_id}"
                collected_games.append(f"{game_player_data.civilization[:2]} {game_player_data.name} <{url}>")
            if len(collected_games) == 0:
                return f"Parsed {parsed_games_count} games. No games match this request"
            collected_games_string = '\n'.join(collected_games)
            return f"""Games that match this request
{collected_games_string}"""


class Social(BaseModel):
    twitch: str | None = None


class Leaderboard(BaseModel):
    rating: int
    rank: int
    rank_level: str | None = None
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
    rm_team: Leaderboard | None = None
    rm_1v1_elo: Leaderboard | None = None
    rm_2v2_elo: Leaderboard | None = None
    rm_3v3_elo: Leaderboard | None = None
    rm_4v4_elo: Leaderboard | None = None


class PlayerSearchResult(BaseModel):
    name: str
    profile_id: int
    steam_id: str
    country: str | None = None
    social: Social
    last_game_at: str
    leaderboards: Leaderboards

    @property
    def last_game_at_arrow(self) -> arrow.Arrow:
        return arrow.get(self.last_game_at)


class PlayerOfTeam(BaseModel):
    profile_id: int
    name: str
    result: str | None
    civilization: str
    civilization_randomized: bool
    rating: int | None
    rating_diff: int | None


class PlayerOfTeamEntry(BaseModel):
    player: PlayerOfTeam


class GameResult(BaseModel):
    game_id: int
    started_at: str
    updated_at: str
    duration: int | None
    map: str
    kind: str
    leaderboard: str
    season: int
    server: str
    patch: int
    average_rating: int | None
    ongoing: bool
    just_finished: bool
    teams: list[list[PlayerOfTeamEntry]]


class FinishedActions(BaseModel):
    feudal_age: list[int] = Field(default_factory=list)
    castle_age: list[int] = Field(default_factory=list)
    imperial_age: list[int] = Field(default_factory=list)
    upgrade_unit_town_center_wheelbarrow_1: list[int] = Field(default_factory=list)
    # TODO More upgrades


class BuildOrderItem(BaseModel):
    id: int | None
    icon: str
    type: str
    finished: list[int]
    constructed: list[int]
    packed: list[int]
    unpacked: list[int]
    transformed: list[int]
    destroyed: list[int]

    @validator("id")
    def format_id(cls, v: str | int | None) -> int | None:
        if v is None:
            return None
        if isinstance(v, int):
            return v
        return int(v.strip())


def format_time(timestamps: list[int]) -> str:
    """From a given list of timestamps, convert them to minute:second format
    E.g. input is [30, 90], output will be "0:30, 1:30"
    """
    times_formatted: list[str] = []
    for timestamp in timestamps:
        minutes, seconds = divmod(timestamp, 60)
        times_formatted.append(f"{minutes}:{seconds:.2f}")
    return ", ".join(times_formatted)


class GamePlayerData(BaseModel):
    profile_id: int
    name: str
    civilization: str
    team: int
    apm: int | None
    actions: FinishedActions
    build_order: list[BuildOrderItem]

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
                raise ValueError(f"Time for villager count must not be 'None'.")
            finished_list = self.finished_list_of_icon('icons/races/common/units/villager')
            if condition.time_in_seconds is None:
                bo_count = len(finished_list)
            else:
                bo_count = sum(1 for i in finished_list if i <= condition.time_in_seconds)
            return bo_count >= condition.target_count
        # TOWNCENTER CONDITION
        if condition.action == Action.TOWNCENTER:
            if condition.time_in_seconds is None:
                raise ValueError(f"Time for villager count must not be 'None'.")
            finished_list = self.finished_list_of_icon('icons/races/common/buildings/town_center')
            if condition.time_in_seconds is None:
                bo_count = len(finished_list)
            else:
                bo_count = sum(1 for i in finished_list if i <= condition.time_in_seconds)
            return bo_count >= condition.target_count
        # FEUDAL CONDITION
        if condition.action == Action.FEUDAL:
            if len(self.actions.feudal_age) == 0:
                return False
            if condition.time_in_seconds is None:
                return True
            if len(self.actions.feudal_age) > 0:
                return self.actions.feudal_age[0] <= condition.time_in_seconds
            return False
        # CASTLE CONDITION
        if condition.action == Action.CASTLE:
            if len(self.actions.castle_age) == 0:
                return False
            if condition.time_in_seconds is None:
                return True
            if len(self.actions.castle_age) > 0:
                return self.actions.castle_age[0] <= condition.time_in_seconds
            return False
        # IMPERIAL CONDITION
        # TODO
        # WHEELBARROW CONDITION
        if condition.action == Action.WHEELBARROW:
            if len(self.actions.upgrade_unit_town_center_wheelbarrow_1) == 0:
                return False
            if condition.time_in_seconds is None:
                return True
            if len(self.actions.upgrade_unit_town_center_wheelbarrow_1) > 0:
                return self.actions.upgrade_unit_town_center_wheelbarrow_1[0] <= condition.time_in_seconds
            return False
        NotImplementedError(f"Not implemented for action: {condition.action}")

    def to_discord_message_towncenters(self) -> str:
        for item in self.build_order:
            if item.icon == 'icons/races/common/buildings/town_center':
                if len(item.constructed) <= 1:
                    return ""
                return f"TCs built at: {format_time(item.constructed[1:])}"
        return ""

    def to_discord_message_villagers(self) -> str:
        count_timestamps_in_minutes = [5, 6, 7, 8, 9, 10]
        villager_counts: list[str] = []
        for item in self.build_order:
            if item.icon == 'icons/races/common/units/villager':
                for max_timestamp in count_timestamps_in_minutes:
                    count = sum(1 for i in item.finished if i < max_timestamp * 60)
                    villager_counts.append(f"{count} ({max_timestamp}m)")
            return ""
        return f"Villagers count: {', '.join(villager_counts)}"

    def to_discord_message_feudal(self) -> str:
        if len(self.actions.feudal_age) == 0:
            return ""
        return f"Feudal reached at: {format_time(self.actions.feudal_age)}"

    def to_discord_message_castle(self) -> str:
        if len(self.actions.castle_age) == 0:
            return ""
        return f"Castle reached at: {format_time(self.actions.castle_age)}"

    def to_discord_message_imperial(self) -> str:
        if len(self.actions.imperial_age) == 0:
            return ""
        return f"Imperial reached at: {format_time(self.actions.imperial_age)}"

    def to_discord_message_wheelbarrow(self) -> str:
        if len(self.actions.upgrade_unit_town_center_wheelbarrow_1) == 0:
            return ""
        return f"Wheelbarrow researched at: {format_time(self.actions.upgrade_unit_town_center_wheelbarrow_1)}"

    def to_discord_message(self) -> str:
        data = [
            self.to_discord_message_towncenters(),
            self.to_discord_message_villagers(),
            self.to_discord_message_feudal(),
            self.to_discord_message_castle(),
            self.to_discord_message_imperial(),
        ]
        info_string = "\n".join(i for i in data if i.strip() != "")
        return info_string


async def search(
    session: aiohttp.ClientSession,
    player_name: str,
) -> AsyncGenerator[PlayerSearchResult, None]:
    """A helper function to search for profiles via a player name query."""
    url = f"https://aoe4world.com/api/v0/players/search?query={player_name}"
    async with session.get(url) as response:
        response: aiohttp.ClientResponse
        if not response.ok:
            return
        data = await response.json()
        for player_data in data["players"]:
            player: PlayerSearchResult = PlayerSearchResult.parse_obj(player_data)
            yield player


async def get_games_by_player_id(session: aiohttp.ClientSession, player_profile_id: int,
                                 allowed_race: str | None) -> AsyncGenerator[GameResult, None]:
    """A helper function that finds the latest games from match history by this player."""
    page = 1
    while 1:
        url = f"https://aoe4world.com/api/v0/games?page={page}&profile_ids={player_profile_id}"
        response = await session.get(url)
        if not response.ok:
            return
        data = await response.json()
        if not data["games"]:
            # End of list reached
            return
        for game_data in data["games"]:
            game_result = GameResult.parse_obj(game_data)
            matches_filter = True
            for team in game_result.teams:
                for player_of_team_entry in team:
                    player = player_of_team_entry.player
                    if allowed_race is not None:
                        if player.civilization[:2] != allowed_race[:2]:
                            matches_filter = False
            if matches_filter:
                yield game_result
        page += 1


async def get_build_order_of_game(
    session: aiohttp.ClientSession,
    game_id: int,
    player_profile_id: int,
) -> GamePlayerData | None:
    """A helper function that gets and parses the build order from a game belonging to a player."""
    url = f"https://aoe4world.com/players/{player_profile_id}/games/{game_id}/summary"
    response = await session.get(url)
    if not response.ok:
        return
    data = await response.json()
    for player_data in data["players"]:
        if player_profile_id != player_data["profile_id"]:
            # Not the player we are looking for
            continue
        # TODO Parse _stats, scores, resources?
        parsed = GamePlayerData.parse_obj(player_data)
        return parsed


async def get_all_games(
    session: aiohttp.ClientSession,
    min_rating: int | None = None,
    max_rating: int | None = None,
    allowed_race: str | None = None,
) -> AsyncGenerator[tuple[GameResult, GamePlayerData], None]:
    page = 1
    if min_rating is None:
        min_rating = 0
    if max_rating is None:
        max_rating = 10_000
    while 1:
        url = f"https://aoe4world.com/api/v0/games?page={page}"
        response = await session.get(url)
        if not response.ok:
            return
        data = await response.json()

        if not data["games"]:
            # No more games
            return

        for game_raw in data["games"]:
            game_result = GameResult.parse_obj(game_raw)
            # Skip ongoing games
            if game_result.ongoing:
                continue
            # Skip short games
            if game_result.duration is None or game_result.duration < 600:
                continue
            for team in game_result.teams:
                for player_of_team_entry in team:
                    if not isinstance(player_of_team_entry, PlayerOfTeamEntry):
                        # Why is this sometimes a list or dict?
                        continue
                    player = player_of_team_entry.player
                    matches_filter = True
                    # Filter race
                    if allowed_race is not None:
                        if player.civilization[:2] != allowed_race[:2]:
                            matches_filter = False
                    # Filter rating
                    if player.rating is not None:
                        if not (min_rating < player.rating < max_rating):
                            matches_filter = False
                    # Yield build order if matches filters, could be multiple per game
                    if matches_filter:
                        build_order_to_yield = await get_build_order_of_game(
                            session, game_result.game_id, player.profile_id
                        )
                        if build_order_to_yield is not None:
                            yield game_result, build_order_to_yield
        page += 1


async def main():
    # Test argument parser

    # Search for player name and return list of players and profiles
    # player_search_query = "burny"
    # data =await public_search_aoe4_players(None, None, player_search_query)

    # If profile_id is given, min_rating and max_rating will be ignored
    # message = "--profile_id 6672615 --race english --condition 2towncenter<600s,wheelbarrow<300s,feudal<360s,castle<720s"

    message = "--race english --condition 2towncenter<900s,wheelbarrow<600s,feudal<600s,castle<900s"
    # message = "--race english --condition 2towncenter<600s,wheelbarrow<300s,feudal<360s,castle<720s"
    data = await public_fetch_aoe4_bo(None, None, message)
    print(data)

    # TODO Analyze game: give information about feudal, tc, wheelbarrow, villagers timestamps
    # message = "--game_id 23457 --profile_id 6672615"
    # data =await public_analyse_aoe4_game(None, None, message)


if __name__ == '__main__':
    asyncio.run(main())
