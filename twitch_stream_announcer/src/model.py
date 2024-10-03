from __future__ import annotations

import os
from collections import OrderedDict

import arrow
import dataset  # pyre-fixme[21]
from dotenv import load_dotenv

load_dotenv()

TABLE_NAME = "stream_announcer_streams"

# pyre-fixme[11]
db: dataset.Database = dataset.connect(os.getenv("POSTGRES_CONNECTION_STRING"))

# pyre-fixme[11]
streams_table: dataset.Table = db[TABLE_NAME]


async def get_streams_to_announce() -> list[OrderedDict]:
    streams = streams_table.find(enabled=True, order_by=["id"])
    return list(streams)


async def set_stream_online(twitch_name: str) -> None:
    db.query(
        f"""UPDATE {TABLE_NAME}
            SET
                status = :new_status,
                announced_at = :current_timestamp
            WHERE twitch_name = :twitch_name""",
        {
            "new_status": "online",
            "current_timestamp": arrow.utcnow().datetime,
            "twitch_name": twitch_name,
        },
    )


async def set_streams_offline(twitch_names: list[str]) -> None:
    assert isinstance(twitch_names, list), type(twitch_names)
    if len(twitch_names) == 0:
        return
    db.query(
        f"""UPDATE {TABLE_NAME}
            SET status = :new_status
            WHERE twitch_name = ANY(:twitch_names)""",
        {
            "new_status": "offline",
            "twitch_names": twitch_names,
        },
    )
