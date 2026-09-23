"""Bot singleton: GatewayBot instance plus shared constants.

Single source of truth for ``bot``, ``BOT_USER_ID``, ``PREFIX``,
``DATA_FOLDER``, ``STAGE`` and ``my_reminder``.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from hikari import GatewayBot  # pyrefly: ignore
from loguru import logger

from commands.public_remind import Remind
from services.startup import create_bot

load_dotenv()

STAGE = os.getenv("STAGE")
assert STAGE in {"DEV", "PROD", "TEST"}, STAGE

bot: GatewayBot = create_bot()
BOT_USER_ID: int = -1

# Discord command prefix
PREFIX = "!"

# Start reminder plugin
my_reminder: Remind = Remind(bot)

# Paths and folders of permanent data
DATA_FOLDER = Path(__file__).parent / "data"
logger.add(DATA_FOLDER / "bot.log")
