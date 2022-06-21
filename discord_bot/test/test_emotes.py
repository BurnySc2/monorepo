from typing import Optional
from unittest.mock import AsyncMock, Mock, patch

import pytest
from hikari import Embed, KnownCustomEmoji, Snowflake
from hypothesis import given
from hypothesis import strategies as st
from postgrest import APIResponse, AsyncSelectRequestBuilder

from commands.public_emotes import TOP_EMOTE_LIMIT, public_count_emotes, public_count_emotes_parser


@given(
    st.booleans(),
    st.booleans(),
    st.booleans(),
    st.one_of(st.none(), st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False)),
)
def test_count_emotes_parser(all_: bool, nostatic: bool, noanimated: bool, days: Optional[int]):
    params = []
    if all_:
        params.append('--all')
    if nostatic:
        params.append('--nostatic')
    if noanimated:
        params.append('--noanimated')
    if days is not None:
        params.append('--days')
        params.append(f'{days}')

    try:
        parsed, unknown_args = public_count_emotes_parser.parse_known_args(args=params)
    except SystemExit:
        return

    assert unknown_args == []
    assert parsed.params.all is all_
    assert parsed.params.nostatic is nostatic
    assert parsed.params.noanimated is noanimated
    assert parsed.params.days == days


# TODO Test error case


def fake_get_emoji(value: int) -> KnownCustomEmoji:
    # pylint: disable=E0110
    return KnownCustomEmoji(
        id=Snowflake(value),
        name='some_emote',
        is_animated=False,
        app=None, # type: ignore
        guild_id=Snowflake(123),
        role_ids=[],
        user=None,
        is_colons_required=False,
        is_managed=False,
        is_available=False,
    )


@pytest.mark.asyncio
async def test_public_count_emotes():
    fake_bot = Mock()
    fake_bot.cache.get_emoji = fake_get_emoji
    fake_event = Mock()
    fake_event.guild_id = 123
    fake_event.author_id = 456
    fake_event.author.username = 'some_username'
    message = '--days 5'
    data = [{'what': '<:some_emote:123456789>'}, {'what': '<:some_emote:123456789>'}]

    with patch.object(AsyncSelectRequestBuilder, 'execute', AsyncMock()) as execute:
        execute.return_value = APIResponse(data=data)
        result = await public_count_emotes(fake_bot, fake_event, message)

    assert isinstance(result, Embed)
    assert result.title == f"{fake_event.author.username}'s top {TOP_EMOTE_LIMIT} used emotes"
    assert result.description == f'Total emotes: {len(data)}\n{len(data)} <:some_emote:123456789>'


# TODO Test various guild, user and emote variations
