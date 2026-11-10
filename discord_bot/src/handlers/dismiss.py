"""Dismiss helpers: X-emoji add and press detection."""

from __future__ import annotations

from hikari import Message  # pyrefly: ignore
from loguru import logger

import bot as bot_module

DISMISS_EMOJI = "\u274c"


async def add_dismiss_emoji(message: Message) -> None:
    try:
        await message.add_reaction(DISMISS_EMOJI)
    except Exception as e:  # noqa: BLE001
        logger.debug(f"Could not add dismiss emoji: {e}")


def is_dismiss_press(*, message: Message, user_id: int, is_for_dismiss_emoji: bool) -> bool:
    if user_id == bot_module.BOT_USER_ID:
        return False
    if message.author.id != bot_module.BOT_USER_ID:
        return False
    return is_for_dismiss_emoji


def is_guild_dismiss_press(*, message: Message, user_id: int, is_for_dismiss_emoji: bool) -> bool:
    return bool(
        is_dismiss_press(message=message, user_id=user_id, is_for_dismiss_emoji=is_for_dismiss_emoji)
        and message.content
        and f"<@{user_id}>" in message.content
    )
