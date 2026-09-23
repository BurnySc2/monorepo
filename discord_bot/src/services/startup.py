"""Bot factory and background startup helpers.

``create_bot`` is the single place that constructs a ``GatewayBot`` so tests
and production share the same construction logic. It defaults to an empty
token so ``STAGE=TEST`` remains importable without ``DISCORD_KEY``.
"""

from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv
from hikari import GatewayBot, Intents  # pyrefly: ignore

load_dotenv()


def create_bot() -> GatewayBot:
    """Create a GatewayBot instance.

    :return: Configured ``GatewayBot`` with ``Intents.ALL``.
    """
    token = os.getenv("DISCORD_KEY", "")
    return GatewayBot(token=token, intents=Intents.ALL)


async def loop_function() -> None:
    """Call ``my_reminder.tick()`` every second forever."""
    # Lazy import to avoid circular import: bot.py imports create_bot from here.
    from bot import my_reminder

    while True:
        await asyncio.sleep(1)
        await my_reminder.tick()
