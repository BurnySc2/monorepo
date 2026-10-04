"""Entry point: exposes shared bot objects and registers event listeners.

All construction lives in :mod:`bot`; business logic lives in
:mod:`handlers.messages`, :mod:`handlers.reactions` and
:mod:`services.message_store`. Exposes ``bot, PREFIX, ...`` for import
and registers listeners on the single shared ``bot`` object.
"""

from __future__ import annotations

import asyncio

from hikari import GuildMessageCreateEvent, GuildReactionAddEvent, StartedEvent  # pyrefly: ignore
from loguru import logger

import bot as bot_module
from bot import BOT_USER_ID, DATA_FOLDER, PREFIX, STAGE, bot, my_reminder

# Shared handler / service exports
from handlers import messages as messages_handler
from handlers import reactions as reactions_handler
from handlers.messages import COMMAND_MAP, generic_command_caller, handle_commands
from handlers.reactions import ALLOWED_EMOJI, DEV_ALLOWED_EMOJI, DEV_TARGET_COUNT, TARGET_COUNT
from services.message_store import (
    add_message_to_db,
    get_all_servers,
    get_text_channels_of_server,
    insert_messages_of_channel_to_db,
)
from services.startup import create_bot, loop_function

__all__ = [
    "ALLOWED_EMOJI",
    "BOT_USER_ID",
    "COMMAND_MAP",
    "DATA_FOLDER",
    "DEV_ALLOWED_EMOJI",
    "DEV_TARGET_COUNT",
    "PREFIX",
    "STAGE",
    "TARGET_COUNT",
    "add_message_to_db",
    "bot",
    "create_bot",
    "generic_command_caller",
    "get_all_servers",
    "get_text_channels_of_server",
    "handle_commands",
    "handle_new_message",
    "handle_reaction_add",
    "insert_messages_of_channel_to_db",
    "loop_function",
    "my_reminder",
    "on_start",
]


@bot.listen()
async def on_start(_event: StartedEvent) -> None:
    global BOT_USER_ID
    logger.info("Bot started")
    BOT_USER_ID = (await bot.rest.fetch_my_user()).id
    # Keep single source of truth in bot.py in sync (handlers read live from there)
    bot_module.BOT_USER_ID = BOT_USER_ID
    # Call another async function that runs forever
    asyncio.create_task(loop_function())
    async for server_name in get_all_servers():
        logger.info(f"Connected to server: {server_name}")


@bot.listen()
async def handle_reaction_add(event: GuildReactionAddEvent) -> None:
    await reactions_handler.handle_reaction_add(event)


@bot.listen()
async def handle_new_message(event: GuildMessageCreateEvent) -> None:
    """Listen for messages being created."""
    channel = event.get_channel()
    if not channel:
        return
    # Use channel 'bot_tests' only for development
    if STAGE == "DEV" and channel.name != "bot_tests":
        return
    if STAGE == "PROD" and channel.name == "bot_tests":
        return

    # Do not react if messages sent by webhook or bot, or message is empty
    if not event.is_human or not event.content:
        return

    # On new message, add message to DB
    await add_message_to_db(event.guild_id, event.channel_id, event.message)

    if event.content is not None and event.content.startswith(PREFIX):
        command, *message_list = event.content.split()
        command = command[len(PREFIX) :]
        message = " ".join(message_list)
        await handle_commands(event, command, message)


# Keep explicit reference so linters do not flag unused shared exports.
_shared_exports = (
    messages_handler,
    reactions_handler,
    DATA_FOLDER,
    STAGE,
    PREFIX,
    my_reminder,
    COMMAND_MAP,
    generic_command_caller,
    handle_commands,
    ALLOWED_EMOJI,
    TARGET_COUNT,
    add_message_to_db,
    get_text_channels_of_server,
    insert_messages_of_channel_to_db,
    get_all_servers,
    create_bot,
    loop_function,
)

if __name__ == "__main__":
    bot.run()
