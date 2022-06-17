import asyncio
from pathlib import Path

from postgrest import APIResponse

from discord_bot.supabase_async_client import Client, create_client

with (Path(__file__).parent / 'SUPABASEURL').open('r') as f:
    url: str = f.read().strip()
with (Path(__file__).parent / 'SUPABASEKEY').open('r') as f:
    key: str = f.read().strip()

supabase: Client = create_client(url, key)


async def main():
    response: APIResponse = await supabase.table('sc2accounts').select('*').execute()

    for row in response.data:
        print(row)

    # End session
    await supabase.postgrest.aclose()


if __name__ == '__main__':
    asyncio.run(main())
