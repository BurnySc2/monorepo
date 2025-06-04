import os

from piccolo.engine.postgres import PostgresEngine

DB = PostgresEngine(
    config={
        "dsn": os.getenv("POSTGRES_CONNECTION_STRING"),
        "database": "discord_bot",
    }
)
