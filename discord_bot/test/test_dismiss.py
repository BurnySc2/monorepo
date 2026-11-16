"""Dismiss helper tests: emoji add + press matrix + guild mention gate."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import hypothesis.strategies as st
import pytest
from hypothesis import example, given, settings

import bot as bot_module
from handlers.dismiss import DISMISS_EMOJI, add_dismiss_emoji, is_dismiss_press, is_guild_dismiss_press

BOT_ID = 123
USER_ID = 7

user_id_strategy = st.one_of(st.sampled_from([BOT_ID, USER_ID, 999]), st.integers(min_value=0, max_value=10_000))
author_id_strategy = st.one_of(st.sampled_from([BOT_ID, USER_ID, 999]), st.integers(min_value=0, max_value=10_000))
emoji_strategy = st.booleans()
content_strategy = st.one_of(
    st.none(),
    st.just(""),
    st.text(max_size=50),
    st.sampled_from([f"hi <@{USER_ID}>", "hi nobody here", f"hi <@{BOT_ID}>"]),
    st.builds(lambda uid: f"hi <@{uid}>", user_id_strategy),
    st.builds(lambda uid, extra: f"{extra} <@{uid}>", user_id_strategy, st.text(max_size=20)),
)


def _make_message(*, author_id=123, content=f"hi <@{USER_ID}>"):
    message = MagicMock()
    message.author.id = author_id
    message.content = content
    message.add_reaction = AsyncMock()
    return message


@pytest.mark.asyncio
async def test_add_dismiss_emoji_reacts_with_cross():
    message = _make_message()
    await add_dismiss_emoji(message)
    message.add_reaction.assert_awaited_once_with(DISMISS_EMOJI)
    assert DISMISS_EMOJI == "\u274c"


@pytest.mark.asyncio
async def test_add_dismiss_emoji_swallows_forbidden():
    message = _make_message()
    message.add_reaction.side_effect = Exception("Forbidden")
    await add_dismiss_emoji(message)
    message.add_reaction.assert_awaited_once_with(DISMISS_EMOJI)


@settings(max_examples=100)
@example(user_id=BOT_ID, author_id=BOT_ID, emoji=True, expected=False)
@example(user_id=USER_ID, author_id=999, emoji=True, expected=False)
@example(user_id=USER_ID, author_id=BOT_ID, emoji=False, expected=False)
@example(user_id=USER_ID, author_id=BOT_ID, emoji=True, expected=True)
@given(
    user_id=user_id_strategy,
    author_id=author_id_strategy,
    emoji=emoji_strategy,
    expected=st.just(None),
)
def test_is_dismiss_press_matrix(user_id, author_id, emoji, expected):
    message = _make_message(author_id=author_id)
    with patch.object(bot_module, "BOT_USER_ID", BOT_ID):
        got = is_dismiss_press(message=message, user_id=user_id, is_for_dismiss_emoji=emoji)
        want = user_id != BOT_ID and author_id == BOT_ID and bool(emoji)
        assert got is want
        if expected is not None:
            assert got is expected


@settings(max_examples=100)
@example(content=f"hi <@{USER_ID}>", user_id=USER_ID, emoji=True, expected=True)
@example(content="hi nobody here", user_id=USER_ID, emoji=True, expected=False)
@example(content=None, user_id=USER_ID, emoji=True, expected=False)
@example(content="", user_id=USER_ID, emoji=True, expected=False)
@example(content=f"hi <@{BOT_ID}>", user_id=BOT_ID, emoji=True, expected=False)
@example(content=f"hi <@{USER_ID}>", user_id=USER_ID, emoji=False, expected=False)
@given(
    content=content_strategy,
    user_id=user_id_strategy,
    emoji=emoji_strategy,
    expected=st.just(None),
)
def test_is_guild_dismiss_press_requires_mention(content, user_id, emoji, expected):
    message = _make_message(author_id=BOT_ID, content=content)
    with patch.object(bot_module, "BOT_USER_ID", BOT_ID):
        base = is_dismiss_press(message=message, user_id=user_id, is_for_dismiss_emoji=emoji)
        got = is_guild_dismiss_press(message=message, user_id=user_id, is_for_dismiss_emoji=emoji)
        want = bool(base and content and f"<@{user_id}>" in content)
        assert got is want
        if expected is not None:
            assert got is expected
