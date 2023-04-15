from unittest.mock import AsyncMock, patch

from hikari import GatewayBot

from main import bot


def test_start_bot():
    # This test should fail if the bot can't launch at all
    with (
        patch.object(GatewayBot, "start", new=AsyncMock()),
        patch.object(GatewayBot, "join", new=AsyncMock()),
    ):
        bot.run()
