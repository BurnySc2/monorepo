"""DM reaction tests: handle_dm_reaction_add dismiss paths."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import bot as bot_module
from handlers.dismiss import DISMISS_EMOJI
from handlers.reactions import handle_dm_reaction_add

BOT_ID = 123
USER_ID = 7


def _make_dm_event(user_id, is_x_emoji):
    event = MagicMock()
    event.user_id = user_id
    event.channel_id = 1
    event.message_id = 2
    event.is_for_emoji = lambda emoji: emoji == DISMISS_EMOJI if is_x_emoji else False
    return event


def _make_message(author_id):
    message = MagicMock()
    message.author.id = author_id
    message.delete = AsyncMock()
    return message


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("author_id", "is_x_emoji"),
    [(USER_ID, True), (BOT_ID, False)],
)
async def test_no_delete(author_id, is_x_emoji):
    event = _make_dm_event(USER_ID, is_x_emoji)
    message = _make_message(author_id)
    with (
        patch.object(bot_module, "BOT_USER_ID", BOT_ID),
        patch.object(bot_module.bot.rest, "fetch_message", new=AsyncMock(return_value=message)),
    ):
        await handle_dm_reaction_add(event)
        message.delete.assert_not_called()


@pytest.mark.asyncio
async def test_happy_path_deletes_once():
    event = _make_dm_event(USER_ID, True)
    message = _make_message(BOT_ID)
    with (
        patch.object(bot_module, "BOT_USER_ID", BOT_ID),
        patch.object(bot_module.bot.rest, "fetch_message", new=AsyncMock(return_value=message)),
    ):
        await handle_dm_reaction_add(event)
        message.delete.assert_awaited_once()
