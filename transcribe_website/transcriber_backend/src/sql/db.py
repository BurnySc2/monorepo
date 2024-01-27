from __future__ import annotations

from pathlib import Path

import psycopg
from loguru import logger

from src.secrets_loader import SECRETS

SECRETS = SECRETS.Transcriber

FOLDER = Path(__file__).parent
CONNECTION_STRING = f"postgresql://{ SECRETS.postgres_user }:{ SECRETS.postgres_password }@{SECRETS.postgres_host}:{SECRETS.postgres_port}/{ SECRETS.postgres_database }"  # noqa: E501


class Queries:
    resume = FOLDER / "downloader/resume.sql"
    mark_filtered = FOLDER / "downloader/mark_filtered.sql"
    get_queued_message = FOLDER / "downloader/get_queued_message.sql"
    get_ids_of_200_messages_from_channel = FOLDER / "downloader/get_ids_of_200_messages_from_channel.sql"
    mark_messages_as = FOLDER / "downloader/mark_messages_as.sql"
    update_completed_message = FOLDER / "downloader/update_completed_message.sql"
    status = FOLDER / "downloader/status.sql"
    count_duplicate = FOLDER / "downloader/count_duplicate.sql"


# TODO Overload functions
# Query may be a file path or string
# If transaction given, dont create new transacton
# If connection given, dont open new connection


def execute_query(
    query_file: Path,
    params: dict | None = None,
    my_row_factory=None,
):
    if params is None:
        params = {}

    # TODO Lock?
    with query_file.open() as f:
        query = f.read()
    with psycopg.connect(
        CONNECTION_STRING,
        autocommit=True,
    ) as conn:
        # statement: str = psycopg.ClientCursor(conn).mogrify(
        #     "SELECT * FROM foo WHERE id = ANY(%s::text[]);", [["10", "20", "30"]]
        # )
        # logger.info(f"Sending query: {statement}")

        # pyre-fixme[6]
        statement: str = psycopg.ClientCursor(conn).mogrify(query, params)
        logger.info(f"Sending query: {statement}")
        # https://www.psycopg.org/psycopg3/docs/basic/usage.html#connection-context
        cur = conn.cursor() if my_row_factory is None else conn.cursor(row_factory=my_row_factory)
        return cur.execute(query, params)
