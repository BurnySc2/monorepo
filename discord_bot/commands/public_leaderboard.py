from __future__ import annotations

import asyncio
from dataclasses import dataclass

import hikari
from hikari import GatewayBot, GuildMessageCreateEvent, Member
from loguru import logger
from postgrest import APIResponse, AsyncSelectRequestBuilder  # pyre-fixme[21]
from simple_parsing import ArgumentParser, field
from table2ascii import Alignment, PresetStyle
from table2ascii import table2ascii as t2a

from db import DiscordMessage, supabase


@dataclass
class LeaderboardParserOptions:
    month: bool = field(alias=["-m"], default=False, action="store_true")
    week: bool = field(alias=["-w"], default=False, action="store_true")
    # rank_range: Optional[str] = field(alias=["-r"], default=None)


public_leaderboard_parser = ArgumentParser()
public_leaderboard_parser.add_arguments(LeaderboardParserOptions, dest="params")  # pyre-fixme[6]


def parse_rank_range_argument(argument_list: list[str]) -> tuple[int, int]:
    """
    Converts the string
    '5-15'
    to tuple
    [5, 15]

    Raises error if too many arguments, or arguments not parseable
    """
    start_rank = 1
    end_rank = 10
    if len(argument_list) > 1:
        raise ValueError
    if len(argument_list) == 1:
        rank_range_arg = argument_list[0]
        if "-" not in rank_range_arg:
            raise LookupError
        rank_range_list = rank_range_arg.split("-")
        try:
            start_rank = int(rank_range_list[0])
            end_rank = int(rank_range_list[1])
            # Sanity check
            if start_rank < 1 or start_rank > end_rank:
                raise ValueError
        except ValueError:
            # Could not parse to int
            raise
        except Exception as e:
            logger.trace(f"Unknown error: {e}")
            raise
    return start_rank, end_rank


async def public_leaderboard(
    bot: GatewayBot,
    event: GuildMessageCreateEvent,
    message: str,
):
    # Pick a random quote
    # TODO Allow to pick a quote of a specific user
    message = message.strip()

    unknown_args: list[str]
    try:
        parsed, unknown_args = public_leaderboard_parser.parse_known_args(args=message.split())
    except SystemExit:
        return

    # Last argument is the rank range argument
    try:
        start_rank, end_rank = parse_rank_range_argument(unknown_args)
    except (ValueError, LookupError) as e:
        logger.trace(f"Parsing rank range error: {e}")
        return
    if end_rank - start_rank >= 20:
        return "Rank range limit is at 20"

    # Get by month, by week, or overall
    if parsed.params.month:
        title = "LEADERBOARD MONTH"
        leaderboard_result = await get_leaderboard_month(event.guild_id, start_rank=start_rank, end_rank=end_rank)
    elif parsed.params.week:
        title = "LEADERBOARD WEEK"
        leaderboard_result = await get_leaderboard_week(event.guild_id, start_rank=start_rank, end_rank=end_rank)
    else:
        title = "GLOBAL LEADERBOARD"
        leaderboard_result = await get_leaderboard_all(event.guild_id, start_rank=start_rank, end_rank=end_rank)

    # No result for this range, or no messages yet, don't send an answer
    if len(leaderboard_result) == 0:
        return

    # Map message author_id's to nicknames
    map_author_id_to_server_nickname: dict[int, str] = {}
    server_members: list[Member] = await bot.rest.fetch_members(event.guild_id)  # pyre-fixme[9]
    for member in server_members:
        map_author_id_to_server_nickname[member.id] = member.display_name

    # Map message author_id's to usernames if they are no longer in the server
    for r in leaderboard_result:
        # Skip if already added as guild member
        if r["author_id"] in map_author_id_to_server_nickname:
            continue
        try:
            user = await bot.rest.fetch_user(r["author_id"])
            map_author_id_to_server_nickname[r["author_id"]] = user.username
        except hikari.errors.NotFoundError:
            # Use author id if not found
            map_author_id_to_server_nickname[r["author_id"]] = r["author_id"]

    data = [
        [
            index,
            r["count"],
            map_author_id_to_server_nickname[r["author_id"]],
        ]
        for index, r in enumerate(leaderboard_result, start=start_rank)
    ]

    # Source: https://stackoverflow.com/a/69574344
    output = t2a(
        header=["Rank", "Count", "Name"],
        body=data,
        style=PresetStyle.thin_compact,
        alignments=[Alignment.RIGHT, Alignment.RIGHT, Alignment.LEFT],
        first_col_heading=True,
    )
    return f"{title}```\n{output}\n```"


async def get_leaderboard_all(server_id: int, start_rank: int, end_rank: int) -> list[dict]:
    query: AsyncSelectRequestBuilder = (  # pyre-fixme[11]
        supabase.table(DiscordMessage.table_name_leaderboard_all())
        .select(
            "guild_id, author_id, count",
        )
        .eq(
            "guild_id",
            server_id,
        )
        .range(  # https://supabase.com/docs/reference/javascript/range
            start_rank - 1,
            end_rank,
        )
    )
    query_response: APIResponse = await query.execute()  # pyre-fixme[11]
    return query_response.data


async def get_leaderboard_month(server_id: int, start_rank: int, end_rank: int) -> list[dict]:
    query: AsyncSelectRequestBuilder = (
        supabase.table(DiscordMessage.table_name_leaderboard_month())
        .select(
            "guild_id, author_id, count",
        )
        .eq(
            "guild_id",
            server_id,
        )
        .range(
            start_rank - 1,
            end_rank,
        )
    )
    query_response: APIResponse = await query.execute()
    return query_response.data


async def get_leaderboard_week(server_id: int, start_rank: int, end_rank: int) -> list[dict]:
    query: AsyncSelectRequestBuilder = (
        supabase.table(DiscordMessage.table_name_leaderboard_week())
        .select(
            "guild_id, author_id, count",
        )
        .eq(
            "guild_id",
            server_id,
        )
        .range(
            start_rank - 1,
            end_rank,
        )
    )
    query_response: APIResponse = await query.execute()
    return query_response.data


async def main() -> None:
    quote = await get_leaderboard_all(384968030423351298, start_rank=1, end_rank=10)
    if quote is None:
        logger.info("No quote could be loaded!")
        return
    logger.info(f"Returned quote: {quote}")


if __name__ == "__main__":
    asyncio.run(main())
