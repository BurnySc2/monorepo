from piccolo.engine.postgres import PostgresEngine

from settings import settings

DB = PostgresEngine(
    config={
        "dsn": settings.postgres_connection_string,
        # Not needed apparently
        # "database": "litestar_server",
    }
)
