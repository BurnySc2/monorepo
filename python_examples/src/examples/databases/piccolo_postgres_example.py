import asyncio
import os
from pathlib import Path

from piccolo.columns import (
    Integer,
    Text,
    JSON,
    JSONB,
    Bytea,
    Boolean,
    Timestamp,
    Timestamptz,
    DoublePrecision,
    UUID,
)
from piccolo.engine.postgres import PostgresEngine
from piccolo.table import Table, create_db_tables
import arrow


# Normally set in "piccolo_conf.py"
db_path = Path(__file__).parent / "temp.db"
DB = PostgresEngine(
    config={
        "dsn": os.getenv("POSTGRES_CONNECTION_STRING"),
        "database": "temp_db",
    }
)
# APP_REGISTRY = AppRegistry(apps=[])


class TestTable(Table, db=DB):
    # "id" field automatically gets added by piccolo
    # id = Serial(required=True)
    temp_bool = Boolean(default=False)
    # Default int4
    temp_int = Integer(default=42)
    # Default float8
    temp_float = DoublePrecision(default=3.14)
    temp_text = Text(default="test")
    temp_bytes = Bytea(default=b"test")
    # Smaller than 'jsonb'
    temp_json = JSON(default={"hello": "world"})
    # Can be parsed compared to 'json'
    temp_jsonb = JSONB(default={"hello": "world"})
    temp_uuid = UUID()
    temp_timestamp = Timestamp(default=arrow.utcnow().naive)
    temp_timestamptz = Timestamptz(default=arrow.utcnow().datetime)


async def run_database_with_piccolo():
    await create_db_tables(TestTable, if_not_exists=True)

    count = await TestTable().count()
    if count < 1:
        # Insert example
        await TestTable().save()

    # Retrieve example
    _temp_row = await TestTable.objects().first()
    "debug entrypoint"


if __name__ == "__main__":
    asyncio.run(run_database_with_piccolo())
