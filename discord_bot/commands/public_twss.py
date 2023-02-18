import asyncio
from pathlib import Path
from typing import Optional, Set

import arrow
from hikari import GatewayBot, GuildMessageCreateEvent
from loguru import logger
from postgrest import APIResponse, AsyncSelectRequestBuilder#pyre-fixme[21]

from db import DiscordQuotes, supabase


async def public_twss(
    _bot: GatewayBot,
    event: GuildMessageCreateEvent,
    _message: str,
):
    # Pick a random quote
    # TODO Allow to pick a quote of a specific user
    quote = await get_random_twss_quote(event.guild_id)
    if quote is None:
        return "Could not find any twss quotes in the database."
    return quote


async def get_random_twss_quote(server_id: int) -> Optional[str]:
    # <YYYY-MM-DD> <Name>: <Message>
    query: AsyncSelectRequestBuilder = (#pyre-fixme[11]
        supabase.table(DiscordQuotes.table_name_random_order_view()).select(
            'when, who, what, emoji_name',
        ).eq(
            "emoji_name",
            "twss",
        ).eq(
            "guild_id",
            server_id,
        ).limit(1)
    )
    query_response: APIResponse = await query.execute()#pyre-fixme[11]
    if not query_response.data:
        return

    for quote in DiscordQuotes.from_select(query_response):
        return f'{quote.when_arrow.strftime("%Y-%m-%d")} {quote.who}: {quote.what}'


async def main() -> None:
    quote = await get_random_twss_quote(384968030423351298)
    if quote is None:
        logger.info("No quote could be loaded!")
        return
    logger.info(f"Returned quote: {quote}")


async def load_csv_to_supabase() -> None:
    path = Path("path_to_file.csv")
    with path.open() as f:
        data = f.readlines()

    query: AsyncSelectRequestBuilder = (supabase.table(DiscordQuotes.table_name()).select('message_id', ))

    # Don't add duplicates
    query_response: APIResponse = await query.execute()
    added_messages: Set[int] = {item['message_id'] for item in query_response.data}

    for row in data:
        if not row.strip():
            continue
        user_id, messge_id, name, *rest = row.split(",")
        time = rest[-1]
        content = ",".join(rest[:-1])
        user_id = user_id.strip("\"")
        messge_id = messge_id.strip("\"")
        name = name.strip("\"")
        content = content.strip("\"")
        time = time.strip("\n").strip("\"")
        time_arrow = arrow.get(time)
        # Add quote to db
        if int(messge_id) in added_messages:
            continue
        await (
            supabase.table(DiscordQuotes.table_name()).insert(
                {
                    'message_id': messge_id,
                    'guild_id': 447056980960346113,
                    'channel_id': 1037477281200877608,
                    'author_id': user_id,
                    'who': name,
                    'when': str(time_arrow.datetime),
                    'what': content,
                    'emoji_name': "twss",
                }
            ).execute()
        )


if __name__ == '__main__':
    asyncio.run(main())
    # asyncio.run(load_csv_to_supabase())
