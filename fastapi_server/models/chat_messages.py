from __future__ import annotations

import os
from typing import Literal

import asyncpg  # pyre-fixme[21]
from asyncpg import Record

assert os.getenv("STAGE", "DEV") in {"DEV", "PROD"}, os.getenv("STAGE")
STAGE: Literal["DEV", "PROD"] = os.getenv("STAGE", "DEV")  # pyre-fixme[9]

TABLE_NAME = f"{STAGE}_chat_messages"


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


async def chat_create_tables() -> None:
    if not await table_exists(TABLE_NAME):
        conn = await create_connection()
        async with conn.transaction():
            # TODO parse timestamp
            await conn.execute(
                f"""
CREATE TABLE {TABLE_NAME} (
id serial PRIMARY KEY,
time_stamp text NOT NULL,
message_author text NOT NULL,
chat_message text NOT NULL
);
INSERT INTO {TABLE_NAME} (time_stamp, message_author, chat_message) VALUES ('4:20:00', 'BuRny', 'Hello world!');
"""
            )


async def get_all_messages() -> list[Record]:
    conn = await create_connection()
    async with conn.transaction():
        # TODO Only get messages <24h old
        return await conn.fetch(
            f"""
SELECT id, time_stamp, message_author, chat_message FROM {TABLE_NAME}
ORDER BY id ASC
LIMIT 100;
"""
        )


async def add_message(time_stamp: str, message_author: str, chat_message: str) -> Record:
    conn = await create_connection()
    async with conn.transaction():
        # TODO use timestamp.now()
        await conn.execute(
            f"""
INSERT INTO {TABLE_NAME} (time_stamp, message_author, chat_message) 
VALUES ($1, $2, $3);
""", time_stamp, message_author, chat_message
        )
        # Assume increasing ids
        row: Record = await conn.fetchrow(
            f"""
SELECT id, time_stamp, message_author, chat_message FROM {TABLE_NAME}
ORDER BY id DESC
LIMIT 1;
"""
        )
        assert row.get("message_author") == message_author
        assert row.get("chat_message") == chat_message
        return row


async def debug_delete_all_messages() -> None:
    conn = await create_connection()
    async with conn.transaction():
        await conn.fetch(f"""
DELETE FROM {TABLE_NAME};
""")
