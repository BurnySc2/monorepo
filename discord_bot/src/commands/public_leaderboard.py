from __future__ import annotations

import asyncio
from dataclasses import dataclass

import hikari
from hikari import GatewayBot, GuildMessageCreateEvent  # pyrefly: ignore
from loguru import logger
from simple_parsing import ArgumentParser, field
from table2ascii import Alignment, PresetStyle
from table2ascii import table2ascii as t2a

from models import DiscordMessage


@dataclass
class LeaderboardParserOptions:
    month: bool = field(alias=["-m"], default=False, action="store_true")
    week: bool = field(alias=["-w"], default=False, action="store_true")
    # rank_range: Optional[str] = field(alias=["-r"], default=None)


public_leaderboard_parser = ArgumentParser()
public_leaderboard_parser.add_arguments(LeaderboardParserOptions, dest="params")


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
    server_members = await bot.rest.fetch_members(event.guild_id)
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
    query = """
SELECT guild_id, author_id, count(*) AS count
FROM discord_message
WHERE guild_id = {}
GROUP BY guild_id, author_id
ORDER BY count DESC
LIMIT {}
OFFSET {};
"""
    return await DiscordMessage.raw(
        query,
        server_id,
        end_rank - start_rank,
        start_rank - 1,
    )


async def get_leaderboard_month(server_id: int, start_rank: int, end_rank: int) -> list[dict]:
    query = """
SELECT guild_id, author_id, count(*) AS count
FROM discord_message
WHERE guild_id = {}
    AND date_trunc('month', now()) < discord_message.when
GROUP BY guild_id, author_id
ORDER BY count DESC
LIMIT {}
OFFSET {};
"""
    return await DiscordMessage.raw(
        query,
        server_id,
        end_rank - start_rank,
        start_rank - 1,
    )


async def get_leaderboard_week(server_id: int, start_rank: int, end_rank: int) -> list[dict]:
    query = """
SELECT guild_id, author_id, count(*) AS count
FROM discord_message
WHERE guild_id = {}
    AND date_trunc('week', now()) < discord_message.when
GROUP BY guild_id, author_id
ORDER BY count DESC
LIMIT {}
OFFSET {};
"""
    return await DiscordMessage.raw(
        query,
        server_id,
        end_rank - start_rank,
        start_rank - 1,
    )


async def main() -> None:
    quote = await get_leaderboard_all(384968030423351298, start_rank=1, end_rank=10)
    if quote is None:
        logger.info("No quote could be loaded!")
        return
    logger.info(f"Returned quote: {quote}")


if __name__ == "__main__":
    asyncio.run(main())
