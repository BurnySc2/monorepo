from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Generator, Literal

import arrow
import toml  # pyre-fixme[21]
from arrow import Arrow
from postgrest.base_request_builder import APIResponse  # pyre-fixme[21]
from pydantic import BaseModel

from supabase_async_client import Client, create_client


class Secrets(BaseModel):
    supabase_url: str = "https://dummyname.supabase.co"
    supabase_key: str = "some.default.key"
    discord_key: str = "somedefaultkey"
    stage: Literal["DEV", "PROD"] = "DEV"


SECRETS_PATH = Path("SECRETS.toml")
assert SECRETS_PATH.is_file(), """Could not find a 'SECRETS.toml' file.
Make sure to enter variables according to the 'Secrets' class."""

with SECRETS_PATH.open() as f:
    SECRETS = Secrets(**toml.loads(f.read()))

supabase: Client = create_client(SECRETS.supabase_url, SECRETS.supabase_key)


class DiscordMessage(BaseModel):
    message_id: int = 0
    guild_id: int = 0
    channel_id: int = 0
    author_id: int = 0
    who: str = ""  # e.g. "BuRny#123456"
    when: str = ""  # e.g. "2021-06-10T11:13:36.522"
    what: str = ""

    @property
    def when_arrow(self) -> Arrow:
        return arrow.get(self.when)

    @staticmethod
    def table_name() -> str:
        return "discord_messages"

    @staticmethod
    def table_name_leaderboard_all() -> str:
        """
                Create view SQL query:
        CREATE VIEW discord_leaderboard_all AS SELECT guild_id, author_id, count(message_id)
        FROM discord_messages AS d
        GROUP BY guild_id, author_id
        ORDER BY count(message_id) DESC;
        """
        return "discord_leaderboard_all"

    @staticmethod
    def table_name_leaderboard_month() -> str:
        """
                Create view SQL query:
        CREATE VIEW discord_leaderboard_month AS SELECT guild_id, author_id, count(message_id)
        FROM discord_messages AS d
        WHERE date_trunc('month', now()) < d.when
        GROUP BY guild_id, author_id
        ORDER BY count(message_id) DESC;
        """
        return "discord_leaderboard_month"

    @staticmethod
    def table_name_leaderboard_week() -> str:
        """
                Create view SQL query:
        CREATE VIEW discord_leaderboard_week AS SELECT guild_id, author_id, count(message_id)
        FROM discord_messages AS d
        WHERE date_trunc('week', now()) < d.when
        GROUP BY guild_id, author_id
        ORDER BY count(message_id) DESC;
        """
        return "discord_leaderboard_week"

    @staticmethod
    def from_select(response: APIResponse) -> Generator[DiscordMessage, None, None]:  # pyre-fixme[11]
        for row in response.data:
            yield DiscordMessage(**row)


class DiscordQuotes(BaseModel):
    # TODO Describe Postgresql schema
    message_id: int = 0
    guild_id: int = 0
    channel_id: int = 0
    author_id: int = 0
    who: str = ""  # e.g. "BuRny#123456"
    when: str = ""  # e.g. "2021-06-10T11:13:36.522"
    what: str = ""
    emoji_name: str = ""  # The name of the emoji, e.g. "twss"

    @property
    def when_arrow(self) -> Arrow:
        return arrow.get(self.when)

    @staticmethod
    def table_name() -> str:
        return "discord_quotes"

    @staticmethod
    def table_name_random_order_view() -> str:
        """
                Create view SQL query:
        CREATE VIEW discord_quotes_random_order_view AS SELECT * FROM discord_quotes ORDER BY random();
        """
        return "discord_quotes_random_order_view"

    @staticmethod
    def from_select(response: APIResponse) -> Generator[DiscordQuotes, None, None]:
        for row in response.data:
            yield DiscordQuotes(**row)


async def main():
    response: APIResponse = await supabase.table(DiscordMessage.table_name()).select("*").limit(10).execute()

    # for message in DiscordMessage.from_select(response):
    for row in response.data:
        _message = DiscordMessage(**row)
        print(row)

    _messages = DiscordMessage.from_select(response)

    # End session
    await supabase.postgrest.aclose()


if __name__ == "__main__":
    asyncio.run(main())
