from __future__ import annotations

import asyncio
import os

import aiohttp
import arrow
from asyncpg import Record
from discord import Embed, Webhook
from dotenv import load_dotenv
from loguru import logger
from model import get_streams_to_announce, set_stream_offline, set_stream_online
from twitchAPI.twitch import Stream, Twitch

load_dotenv()


def group_my_rows(data: list[Record]) -> dict[str, list[list]]:
    grouped = {}
    for i in data:
        twitch_name = i.get("twitch_name")
        if twitch_name in grouped:
            grouped[twitch_name].append(i)
        else:
            grouped[twitch_name] = [i]
    return grouped


async def check_twitch(grouped_data: dict[str, list[Record]]):
    twitch = await Twitch(
        os.getenv("TWITCH_APP_ID"),
        os.getenv("TWITCH_APP_SECRET"),
    )
    session = aiohttp.ClientSession()
    for twitch_username, data in grouped_data.items():
        stream_info: Stream
        async for stream_info in twitch.get_streams(user_login=[twitch_username]):
            stream_is_online: bool = stream_info.type == "live"
            stream_online_since: arrow.Arrow = arrow.get(stream_info.started_at)
            for row in data:
                if stream_is_online:
                    # Stream is online: notify and write to db
                    # If stream was offline previously and hasn't been announced yet, announce it
                    last_announced: arrow.Arrow = arrow.get(row.get("announced_at"))
                    diff = arrow.now() - last_announced
                    if diff.total_seconds() > int(os.getenv("OFFLINE_GRACE_TIME")):
                        # Announce stream being online in webhook
                        await send_webhook(
                            twitch_username,
                            stream_online_since,
                            session,
                            row,
                            stream_info,
                        )
                    # Update in db
                    await set_stream_online(twitch_username)
                else:
                    await set_stream_offline(twitch_username)


async def send_webhook(
    twitch_username: str,
    stream_online_since: arrow.Arrow,
    session: aiohttp.ClientSession,
    row: list[Record],
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
    rows: list[Record] = await get_streams_to_announce()
    grouped_rows: dict[str, list[Record]] = group_my_rows(rows)
    await check_twitch(grouped_rows)


if __name__ == "__main__":
    asyncio.run(main())
