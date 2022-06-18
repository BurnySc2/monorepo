import asyncio
import os
from pathlib import Path
from typing import Generator

from postgrest.base_request_builder import APIResponse

from discord_bot.supabase_async_client import Client, create_client

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


def flatten_result(result: APIResponse, column_name: str) -> Generator:
    # If 'select' only queried one column, flatten result to an iterator
    for row in result.data:
        yield row[column_name]


async def main():
    response: APIResponse = await supabase.table('sc2accounts').select('*').execute()

    for row in response.data:
        print(row)

    # End session
    await supabase.postgrest.aclose()


if __name__ == '__main__':
    asyncio.run(main())
