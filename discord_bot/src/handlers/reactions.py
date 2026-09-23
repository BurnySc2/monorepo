"""Reaction handlers: delete-on-X and twss-quote logic.

Reaction handlers with test-visible constants. ``BOT_USER_ID`` is read live
from :mod:`bot` so ``on_start`` updates are always visible.
"""

from __future__ import annotations

from hikari import GuildReactionAddEvent, Message  # pyrefly: ignore
from loguru import logger

import bot as bot_module
from models import DiscordQuote

ALLOWED_EMOJI: set[str] = {"twss"}
TARGET_COUNT: int = 3

# Development overrides for the ``bot_tests`` channel.
DEV_ALLOWED_EMOJI: set[str] = {"burnysStalker"}
DEV_TARGET_COUNT: int = 1


def get_allowed_emoji(channel_name: str) -> tuple[set[str], int]:
    """Return (allowed_emoji_names, target_emoji_count) for a channel."""
    if bot_module.STAGE == "DEV" and channel_name == "bot_tests":
        return DEV_ALLOWED_EMOJI, DEV_TARGET_COUNT
    return ALLOWED_EMOJI, TARGET_COUNT


async def handle_reaction_add(event: GuildReactionAddEvent) -> None:
    if event.member.is_bot:
        return

    channel = await bot_module.bot.rest.fetch_channel(event.channel_id)
    # Use channel 'bot_tests' only for development
    if bot_module.STAGE == "DEV" and channel.name != "bot_tests":
        return
    if bot_module.STAGE == "PROD" and channel.name == "bot_tests":
        return

    message: Message = await bot_module.bot.rest.fetch_message(event.channel_id, event.message_id)
    if not message:
        return

    # Message is by bot
    # Message has mention
    # Mention is same user who reacted
    # Remove message if :x: was reacted to it
    if (
        message.author.id == bot_module.BOT_USER_ID
        and message.content
        and f"<@{event.user_id}>" in message.content
        and event.is_for_emoji("\u274c")
    ):
        await message.delete()
        return

    # If "twss" reacted and reaction count >=3: add quote to db
    allowed_emoji_names, target_emoji_count = get_allowed_emoji(channel.name)
    if not message.author.is_bot and event.emoji_name in allowed_emoji_names:
        for reaction in message.reactions:
            if reaction.emoji.name in allowed_emoji_names and reaction.count >= target_emoji_count:
                # Add quote to db
                if bot_module.STAGE == "PROD":
                    await DiscordQuote(
                        message_id=message.id,
                        guild_id=event.guild_id,
                        channel_id=event.channel_id,
                        author_id=message.author.id,
                        who=str(message.author),
                        when=message.created_at,
                        what=message.content,
                        emoji_name=reaction.emoji.name,
                    ).save()
                logger.info(f"Added quote: {message.content}")

                # Notify people in channel that a quote has been added
                # TODO and how many there are now in total
                response_message = (
                    f"Added {reaction.emoji.name} quote:\n{message.created_at.strftime('%Y-%m-%d')} "
                    f"{str(message.author)}: {message.content}"
                )
                await channel.send(response_message)  # pyrefly: ignore
                return
