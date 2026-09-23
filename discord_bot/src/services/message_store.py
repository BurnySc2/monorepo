"""Persistence helpers for Discord messages and guild traversal
using the singleton ``bot``/``STAGE`` from :mod:`bot`.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import suppress
from typing import Any

import hikari.errors
from asyncpg.exceptions import UniqueViolationError
from hikari import GuildTextChannel, Message, OwnGuild  # pyrefly: ignore
from hikari.channels import ChannelType
from loguru import logger

import bot as bot_module
from models import DiscordMessage

# Re-export singleton for convenience; always access via bot_module for freshness.
bot = bot_module.bot


async def get_text_channels_of_server(server: OwnGuild) -> AsyncGenerator[GuildTextChannel, None]:
    assert isinstance(server, OwnGuild), type(server)
    for channel in await bot_module.bot.rest.fetch_guild_channels(server):
        if channel.type not in {ChannelType.GUILD_TEXT}:
            continue
        assert isinstance(channel, GuildTextChannel), type(channel)
        yield channel


async def add_message_to_db(server_id: int, channel_id: int, message: Message) -> None:
    """Insert message into database."""
    if message.content is None:
        return
    # duplicate key value violates unique constraint "discord_message_message_id_key"
    with suppress(UniqueViolationError):
        await DiscordMessage(
            message_id=message.id,
            guild_id=server_id,
            channel_id=channel_id,
            author_id=message.author.id,
            who=str(message.author),
            when=message.created_at,
            what=message.content,  # TODO Ignore text
        ).save()


async def insert_messages_of_channel_to_db(server: OwnGuild, channel: GuildTextChannel) -> None:
    # Check if bot has access to channel
    if channel.last_message_id is None:
        return
    try:
        _temp_message = await channel.fetch_message(channel.last_message_id)
    except hikari.errors.ForbiddenError:
        logger.error(f"No access to channel '{channel}' in server '{server}'")
        return
    except hikari.errors.NotFoundError:
        logger.error(f"Last message in channel '{channel}' in server '{server}' could not be fetched")
        return

    # Grab message ids to not insert duplicates
    messages = await DiscordMessage.select(DiscordMessage.message_id)
    message_ids: set[int] = {message["message_id"] for message in messages}

    messages_inserted_count = 0
    async for message in channel.fetch_history():
        # Don't process duplicates
        if message.id in message_ids:
            continue
        # Ignore bot and webhook messages
        if message.author.is_bot:
            continue
        # TODO Use bulk insert via List[dict] once API allows it
        # logger.info(f"Inserting message from {message.created_at}")
        await add_message_to_db(server.id, channel.id, message)
        messages_inserted_count += 1
    if messages_inserted_count > 0:
        logger.info(f"Inserted {messages_inserted_count} messages of channel '{channel}' in server '{server}'")


async def get_all_servers() -> AsyncGenerator[OwnGuild, Any]:
    server: OwnGuild
    async for server in bot_module.bot.rest.fetch_my_guilds():
        yield server
        if bot_module.STAGE == "PROD":
            # Add all messages to DB
            async for channel in get_text_channels_of_server(server):
                # Create a coroutine that works in background to add messages of specific server and channel to database
                asyncio.create_task(insert_messages_of_channel_to_db(server, channel))
