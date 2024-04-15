from __future__ import annotations

import asyncio
import os
from collections import OrderedDict

import aiohttp
import arrow
from discord import Embed, Webhook
from dotenv import load_dotenv
from loguru import logger
from model import get_streams_to_announce, set_stream_online, set_streams_offline  # pyre-fixme[21]
from twitchAPI.twitch import Stream, Twitch

load_dotenv()

# pyre-fixme[6]
OFFLINE_GRACE_TIME = int(os.getenv("OFFLINE_GRACE_TIME"))
assert OFFLINE_GRACE_TIME > 0


def group_my_rows(data: list[OrderedDict]) -> dict[str, list[OrderedDict]]:
    grouped = {}
    for row in data:
        twitch_name = row["twitch_name"]
        if twitch_name not in grouped:
            grouped[twitch_name] = []
        grouped[twitch_name].append(row)
    return grouped


def chunk_data(grouped_data: dict[str, list[OrderedDict]], size: int = 20) -> list[dict[str, OrderedDict]]:
    chunked_data: list[dict] = []
    for twitch_username in grouped_data:
        if len(chunked_data) == 0:
            chunked_data.append({})
        if len(chunked_data[-1]) == size:
            chunked_data.append({})
        chunked_data[-1][twitch_username] = grouped_data[twitch_username]
    return chunked_data


async def check_twitch(chunked_data: list[dict[str, OrderedDict]]):
    twitch = await Twitch(
        # pyre-fixme[6]
        os.getenv("TWITCH_APP_ID"),
        os.getenv("TWITCH_APP_SECRET"),
    )
    session = aiohttp.ClientSession()
    all_previously_online_streams: list[str] = [
        db_entry["twitch_name"] for chunk in chunked_data for db_entries in chunk.values() for db_entry in db_entries
        if db_entry.get("status") == "online"
    ]
    all_online_streams: list[str] = []
    for chunk in chunked_data:
        twitch_usernames = list(chunk.keys())
        logger.info(f"Checking '{twitch_usernames}'...")
        stream_info: Stream
        # Seems to only return results if stream is online
        async for stream_info in twitch.get_streams(user_login=twitch_usernames):
            stream_is_online: bool = stream_info.type == "live"
            stream_online_since: arrow.Arrow = arrow.get(stream_info.started_at)
            twitch_username = stream_info.user_name
            twitch_username_db = stream_info.user_login
            if stream_is_online:
                all_online_streams.append(twitch_username_db)
                for stream_info_row in chunk[stream_info.user_login]:
                    # Stream is online: notify and write to db
                    # If stream was offline previously and hasn't been announced yet, announce it
                    last_announced: arrow.Arrow = arrow.get(stream_info_row.get("announced_at") or 0)
                    diff = arrow.now() - last_announced
                    if diff.total_seconds() > OFFLINE_GRACE_TIME:
                        # Announce stream being online in webhook
                        await send_webhook(
                            twitch_username,
                            stream_online_since,
                            session,
                            stream_info_row,
                            stream_info,
                        )
                # Update in db
                await set_stream_online(twitch_username_db)
    now_offline_streams: list[str] = list(set(all_previously_online_streams) - set(all_online_streams))
    await set_streams_offline(now_offline_streams)
    await session.close()


async def send_webhook(
    twitch_username: str,
    stream_online_since: arrow.Arrow,
    session: aiohttp.ClientSession,
    row: OrderedDict,
    stream_info: Stream,
):
    webhook = Webhook.from_url(row.get("discord_webhook"), session=session)
    webhook_message = row.get("announce_message")
    discord_webhook_url = row.get("discord_webhook")
    webhook_embed = Embed(
        title=f"{stream_info.user_name} is now live on Twitch!",
        url=f"https://twitch.tv/{twitch_username}",
    )

    stream_title = "No stream title set"
    if stream_info.title:
        stream_title = stream_info.title
    webhook_embed.add_field(name="Stream title", value=f"{stream_title}", inline=False)

    webhook_embed.add_field(
        name=f"Playing '{stream_info.game_name}'",
        value=f"since {stream_online_since.isoformat()} (which was {stream_online_since.humanize()})",
        inline=False,
    )
    logger.info(f"Sending webhook to {discord_webhook_url} because stream {twitch_username} is online!")
    await webhook.send(webhook_message, username="Stream Announcer Webhook", embed=webhook_embed)


async def main():
    rows: list[OrderedDict] = await get_streams_to_announce()
    grouped_rows: dict[str, list[OrderedDict]] = group_my_rows(rows)
    chunked_data = chunk_data(grouped_rows)
    await check_twitch(chunked_data)


if __name__ == "__main__":
    asyncio.run(main())
