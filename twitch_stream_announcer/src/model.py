from __future__ import annotations

import datetime
import os

import asyncpg  # pyre-fixme[21]
from asyncpg import Record
from dotenv import load_dotenv

load_dotenv()

TABLE_NAME = "stream_announcer_streams"
a = os.environ


# pyre-fixme[11]
async def create_connection() -> asyncpg.Connection:
    # TODO use 'with' statement of possible
    return await asyncpg.connect(
        os.getenv("POSTGRES_CONNECTION_STRING"),
        timeout=60,  # Allow max 60 seconds per connection
    )


async def table_exists(table_name: str) -> bool:
    conn = await create_connection()
    # pyre-fixme[11]
    data: Record = await conn.fetchrow(
        """
SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name ILIKE $1);
""", table_name
    )
    return data.get("exists")


async def get_streams_to_announce() -> list[Record]:
    conn = await create_connection()
    async with conn.transaction():
        return await conn.fetch(
            f"""SELECT twitch_name, discord_webhook, announce_message, announced_at, status
            FROM {TABLE_NAME}
            WHERE enabled = true
            ORDER BY id ASC"""
        )


async def set_stream_online(twitch_name: str) -> None:
    conn = await create_connection()
    async with conn.transaction():
        await conn.execute(
            f"""UPDATE {TABLE_NAME}
            SET status = $1, announced_at = $2
            WHERE twitch_name = $3""",
            "online",
            datetime.datetime.utcnow(),
            twitch_name,
        )


async def set_stream_offline(twitch_name: str) -> None:
    conn = await create_connection()
    async with conn.transaction():
        await conn.execute(
            f"""UPDATE {TABLE_NAME}
            SET status = $1
            WHERE twitch_name = $2""",
            "offline",
            twitch_name,
        )
