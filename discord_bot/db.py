from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Generator

import arrow
from arrow import Arrow
from postgrest.base_request_builder import APIResponse

from supabase_async_client import Client, create_client

# Load url and key from env or from file

url: str = os.getenv('SUPABASEURL')  # type: ignore
if url is None:
    SUPABASEURL_PATH = Path(__file__).parent / 'SUPABASEURL'
    assert SUPABASEURL_PATH.is_file(
    ), f'Missing file with supabase url: {SUPABASEURL_PATH}, you can get it from https://app.supabase.com/project/<project_id>/settings/api'
    with SUPABASEURL_PATH.open('r') as f:
        url = f.read().strip()
key: str = os.getenv('SUPABASEKEY')  # type: ignore
if key is None:
    SUPABASEKEY_PATH = Path(__file__).parent / 'SUPABASEKEY'
    assert SUPABASEKEY_PATH.is_file(
    ), f'Missing file with supabase key: {SUPABASEKEY_PATH}, you can get it from https://app.supabase.com/project/<project_id>/settings/api'
    with SUPABASEKEY_PATH.open('r') as f:
        key = f.read().strip()

supabase: Client = create_client(url, key)
del url
del key


@dataclass
class DiscordMessage:
    message_id: int = 0
    guild_id: int = 0
    channel_id: int = 0
    author_id: int = 0
    who: str = ''  # e.g. "BuRny#123456"
    when: str = ''  # e.g. "2021-06-10T11:13:36.522"
    what: str = ''

    @property
    def when_arrow(self) -> Arrow:
        return arrow.get(self.when)

    @staticmethod
    def table_name() -> str:
        return 'discord_messages'

    @staticmethod
    def table_name_leaderboard_all() -> str:
        return 'discord_leaderboard_all'

    @staticmethod
    def table_name_leaderboard_month() -> str:
        return 'discord_leaderboard_month'

    @staticmethod
    def table_name_leaderboard_week() -> str:
        return 'discord_leaderboard_week'

    @staticmethod
    def from_select(response: APIResponse) -> Generator[DiscordMessage, None, None]:
        for row in response.data:
            yield DiscordMessage(**row)


@dataclass
class DiscordQuotes:
    message_id: int = 0
    guild_id: int = 0
    channel_id: int = 0
    author_id: int = 0
    who: str = ''  # e.g. "BuRny#123456"
    when: str = ''  # e.g. "2021-06-10T11:13:36.522"
    what: str = ''
    emoji_name: str = ''  # The name of the emoji, e.g. "twss"

    @property
    def when_arrow(self) -> Arrow:
        return arrow.get(self.when)

    @staticmethod
    def table_name() -> str:
        return 'discord_quotes'

    @staticmethod
    def table_name_random_order_view() -> str:
        return 'discord_quotes_random_order_view'

    @staticmethod
    def from_select(response: APIResponse) -> Generator[DiscordQuotes, None, None]:
        for row in response.data:
            yield DiscordQuotes(**row)


async def main():
    response: APIResponse = await supabase.table(DiscordMessage.table_name()).select('*').limit(10).execute()

    # for message in DiscordMessage.from_select(response):
    for row in response.data:
        _message = DiscordMessage(**row)
        print(row)

    _messages = DiscordMessage.from_select(response)

    # End session
    await supabase.postgrest.aclose()


if __name__ == '__main__':
    asyncio.run(main())
