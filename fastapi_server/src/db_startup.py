"""Create missing database tables and indexes at server startup (idempotent)."""

from pathlib import Path

from loguru import logger
from piccolo.table import Table, create_db_tables

from models.raceroom import ensure_raceroom_schema
from models.telegram_browser import TelegramChannel, TelegramDownload, TelegramMessage
from schemas.audiobook.db_models import AudiobookBook, AudiobookChapter

_QUERIES_DIR = Path(__file__).parent / "queries"

# create_db_tables sorts by foreign keys; the order here is only for readability.
SERVICE_TABLES: tuple[type[Table], ...] = (
    AudiobookBook,
    AudiobookChapter,
    TelegramChannel,
    TelegramMessage,
    TelegramDownload,
)


def _read_query(name: str) -> str:
    """Read a SQL statement from the queries directory."""
    return (_QUERIES_DIR / name).read_text(encoding="utf-8")


async def create_tables() -> None:
    """Create every table this server owns."""
    await create_db_tables(*SERVICE_TABLES, if_not_exists=True)
    await ensure_raceroom_schema()


async def create_telegram_indexes() -> None:
    """Create the Telegram indexes if they are missing. Their tables must already exist."""
    await TelegramMessage.raw(_read_query("telegram_browser_message_unique_index.sql"))
    await TelegramMessage.raw(_read_query("telegram_browser_indexes.sql"))


async def initialize_database() -> None:
    """Create tables first, then indexes, because indexes need their tables."""
    await create_tables()
    await create_telegram_indexes()
    logger.info("Database tables and indexes are ready")
