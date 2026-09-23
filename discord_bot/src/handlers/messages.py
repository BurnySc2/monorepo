"""Message command dispatch: generic caller, command map, and handlers.

Uses the singleton ``bot``/``my_reminder`` from :mod:`bot` so there is exactly one bot object.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from hikari import Embed, GatewayBot, GuildMessageCreateEvent  # pyrefly: ignore

import bot as bot_module
from commands.public_fetch_aoe4 import (
    public_analyse_aoe4_game,
    public_fetch_aoe4_bo,
    public_search_aoe4_players,
)
from commands.public_leaderboard import public_leaderboard
from commands.public_mmr import public_mmr
from commands.public_twss import public_twss

# Dispatch table: command string (without PREFIX) -> handler.
# Built lazily via function to avoid import-time binding issues in tests,
# Also exposed as COMMAND_MAP const for direct import and tests.
COMMAND_MAP: dict[str, Callable[[GatewayBot, GuildMessageCreateEvent, str], Awaitable[Embed | str | None]]] = {
    "reminder": bot_module.my_reminder.public_remind_in,
    "r": bot_module.my_reminder.public_remind_in,
    "remindat": bot_module.my_reminder.public_remind_at,
    "ra": bot_module.my_reminder.public_remind_at,
    "reminders": bot_module.my_reminder.public_list_reminders,
    "delreminder": bot_module.my_reminder.public_del_remind,
    "dr": bot_module.my_reminder.public_del_remind,
    "mmr": public_mmr,
    # "emotes": public_count_emotes,
    "twss": public_twss,
    "leaderboard": public_leaderboard,
    "aoe4find": public_search_aoe4_players,
    "aoe4search": public_search_aoe4_players,
    "aoe4bo": public_fetch_aoe4_bo,
    "aoe4analyse": public_analyse_aoe4_game,
    "aoe4analyze": public_analyse_aoe4_game,
}


async def generic_command_caller(
    event: GuildMessageCreateEvent,
    function_to_call: Callable[[GatewayBot, GuildMessageCreateEvent, str], Awaitable[Embed | str | None]],
    message: str,
    add_remove_emoji: bool = False,
) -> None:
    """
    @param event
    @param function_to_call: A function to be called with the given message,
    expects function to return an Embed or string
    @param message: Parsed messaged by the user, without the command
    @param add_remove_emoji: If true, bot will react to its own message with a 'X' emoji
    so that the mentioned user can remove the bot message at will.
    """
    channel = event.get_channel()
    if not channel:
        return

    # Call the given function with the bot, event and message
    response: Embed | str | None = await function_to_call(bot_module.bot, event, message)
    if response is None:
        # Function errored or no results
        return

    if isinstance(response, Embed):
        sent_message = await event.message.respond(f"{event.author.mention}", embed=response, reply=False)
    else:
        # Error message or raw string response
        sent_message = await event.message.respond(f"{event.author.mention} {response}", reply=False)
    if add_remove_emoji:
        # https://www.fileformat.info/info/unicode/char/274c/index.htm
        await sent_message.add_reaction("\u274c")


async def handle_commands(event: GuildMessageCreateEvent, command: str, message: str) -> None:
    if command in COMMAND_MAP:
        function = COMMAND_MAP[command]
        await generic_command_caller(
            event,
            function,  # pyrefly: ignore
            message,
            add_remove_emoji=True,
        )

    if command == "ping":
        guild = event.get_guild()
        if not guild:
            return
        b = await guild.fetch_emojis()

        animated = next(i for i in b if i.is_animated)
        await event.message.respond(f"Pong! {bot_module.bot.heartbeat_latency * 1_000:.0f}ms {b[0]} {animated}")
