"""Handler tests: dispatch table + generic caller Embed/str + reaction flag."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hikari import Embed  # pyrefly: ignore

from handlers.messages import COMMAND_MAP, generic_command_caller, handle_commands


def _make_event(channel=None, mention="@user"):
    event = MagicMock()
    event.get_channel.return_value = channel
    event.author.mention = mention
    event.message.respond = AsyncMock()
    return event


def _make_sent_message():
    sent = MagicMock()
    sent.add_reaction = AsyncMock()
    return sent


def test_command_map_contains_expected_keys():
    expected = {
        "reminder",
        "r",
        "remindat",
        "ra",
        "reminders",
        "delreminder",
        "dr",
        "mmr",
        "twss",
        "leaderboard",
        "aoe4find",
        "aoe4search",
        "aoe4bo",
        "aoe4analyse",
        "aoe4analyze",
    }
    assert expected.issubset(set(COMMAND_MAP.keys()))


def test_command_map_aliases_share_handler():
    assert COMMAND_MAP["reminder"] == COMMAND_MAP["r"]
    assert COMMAND_MAP["remindat"] == COMMAND_MAP["ra"]
    assert COMMAND_MAP["delreminder"] == COMMAND_MAP["dr"]
    assert COMMAND_MAP["aoe4find"] == COMMAND_MAP["aoe4search"]
    assert COMMAND_MAP["aoe4analyse"] == COMMAND_MAP["aoe4analyze"]


def test_command_map_targets_real_functions():
    from commands.public_mmr import public_mmr
    from commands.public_twss import public_twss
    from commands.public_leaderboard import public_leaderboard

    assert COMMAND_MAP["mmr"] is public_mmr
    assert COMMAND_MAP["twss"] is public_twss
    assert COMMAND_MAP["leaderboard"] is public_leaderboard


@pytest.mark.asyncio
async def test_generic_caller_embed_no_reaction():
    channel = MagicMock()
    event = _make_event(channel=channel, mention="<@123>")
    sent = _make_sent_message()
    event.message.respond.return_value = sent

    embed = Embed(title="t", description="d")

    async def fake_fn(_bot, _event, _msg):
        return embed

    await generic_command_caller(event, fake_fn, "hello", add_remove_emoji=False)

    event.message.respond.assert_awaited_once()
    _, kwargs = event.message.respond.call_args
    assert kwargs.get("embed") is embed
    sent.add_reaction.assert_not_called()


@pytest.mark.asyncio
async def test_generic_caller_str_with_reaction_flag():
    channel = MagicMock()
    event = _make_event(channel=channel, mention="<@456>")
    sent = _make_sent_message()
    event.message.respond.return_value = sent

    async def fake_fn(_bot, _event, _msg):
        return "some text"

    await generic_command_caller(event, fake_fn, "hello", add_remove_emoji=True)

    event.message.respond.assert_awaited_once()
    args, _kwargs = event.message.respond.call_args
    assert "<@456>" in args[0]
    assert "some text" in args[0]
    sent.add_reaction.assert_awaited_once_with("\u274c")


@pytest.mark.asyncio
async def test_generic_caller_none_response_does_nothing():
    channel = MagicMock()
    event = _make_event(channel=channel)
    sent = _make_sent_message()
    event.message.respond.return_value = sent

    async def fake_fn(_bot, _event, _msg):
        return None

    await generic_command_caller(event, fake_fn, "hello", add_remove_emoji=True)

    event.message.respond.assert_not_called()
    sent.add_reaction.assert_not_called()


@pytest.mark.asyncio
async def test_generic_caller_no_channel_early_return():
    event = _make_event(channel=None)
    called = False

    async def fake_fn(_bot, _event, _msg):
        nonlocal called
        called = True
        return "hi"

    await generic_command_caller(event, fake_fn, "hello")
    assert called is False
    event.message.respond.assert_not_called()


@pytest.mark.asyncio
async def test_handle_commands_dispatches_via_table():
    event = MagicMock()
    with patch("handlers.messages.generic_command_caller", new=AsyncMock()) as caller_mock:
        await handle_commands(event, "mmr", "some player")
        caller_mock.assert_awaited_once()
        _args, kwargs = caller_mock.call_args
        # Called with add_remove_emoji=True per PREFIX semantics
        assert kwargs.get("add_remove_emoji") is True or _args[3] is True


@pytest.mark.asyncio
async def test_handle_commands_unknown_does_nothing():
    event = MagicMock()
    event.get_guild.return_value = None
    with patch("handlers.messages.generic_command_caller", new=AsyncMock()) as caller_mock:
        await handle_commands(event, "unknown_cmd_xyz", "msg")
        caller_mock.assert_not_called()
