import asyncio
import datetime
import re

import arrow
import httpx
from loguru import logger
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from models.raceroom import RRREBestTime, RRREPlayer, RRRETrack
from settings import settings

TRACK_IDS = [
    # Oschersleben
    12506,
    # Silverstone
    4039,
    # Spielberg
    2556,
]


class BestTime(BaseModel):
    player_id: int
    player_name: str
    track_id: int
    track_name: str
    car_class: str
    car_name: str
    driving_model: str  # Difficulty
    datetime_driven: str
    datetime_driven_parsed: datetime.datetime
    best_time: str
    best_time_parsed: float


_AVATAR_ID_RE = re.compile(r"/user_avatar/([0-9]+)(?:[/?#]|$)")


def parse_player_id(driver: dict) -> int | None:
    """Return the numeric driver id from the avatar URL, or None when unavailable.

    The avatar URL ends in the numeric user id
    (``https://game.raceroomracing.com/game/user_avatar/1233502``). Name-only
    paths such as ``/users/Fogino`` carry no id; ``None`` makes the caller skip
    that row instead of crashing the whole track.
    """
    match = _AVATAR_ID_RE.search(driver.get("avatar") or "")
    if match is not None:
        return int(match.group(1))
    return None


def parse_laptime(laptime: str) -> float:
    match = re.fullmatch(r"(\d+)m (\d+\.\d+)s(?:, .+)?", laptime)
    if match is None:
        raise ValueError(f"Laptime not parseable: {laptime}")
    minutes, seconds = match.groups()
    return int(minutes) * 60 + float(seconds)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(httpx.HTTPError),
    reraise=True,
)
async def fetch_track_info(client: httpx.AsyncClient, track_id: int, car_class: str = "class-5262") -> list[BestTime]:
    url = f"https://game.raceroom.com/leaderboard/listing/0?start=0&count=200&track={track_id}&car_class={car_class}"
    response = await client.get(
        url,
        # Header required to receive data as json
        headers={"x-requested-with": "XMLHttpRequest"},
    )
    # Raise httpx.HTTPStatusError (a subclass of httpx.HTTPError) so
    # transient HTTP failures are retried by the decorator above.
    response.raise_for_status()
    data = response.json()

    results = data["context"]["c"]["results"]
    data_parsed: list[BestTime] = []
    skipped = 0
    for i in results:
        player_id = parse_player_id(i["driver"])
        if player_id is None:
            logger.warning(
                "Skipping result without parsable driver id: path={} avatar={} name={} track_id={}",
                i["driver"].get("path"),
                i["driver"].get("avatar"),
                i["driver"].get("name"),
                track_id,
            )
            skipped += 1
            continue
        data_parsed.append(
            BestTime(
                player_id=player_id,
                player_name=i["driver"]["name"],
                track_id=track_id,
                track_name=i["track"]["name"],
                car_class=i["car_class"]["car"]["class-name"],
                car_name=i["car_class"]["car"]["name"],
                driving_model=i["driving_model"],
                datetime_driven=i["date_time"],
                datetime_driven_parsed=arrow.get(i["date_time"]).naive,
                best_time=i["laptime"],
                best_time_parsed=parse_laptime(i["laptime"]),
            )
        )
    if skipped:
        log = logger.error if skipped == len(results) else logger.warning
        log("Skipped {} of {} results for track_id={}", skipped, len(results), track_id)
    return data_parsed


async def update_db_data(results: list[BestTime], track_id: int) -> None:
    # Nothing to update
    if len(results) == 0:
        logger.warning("No data to update for track_id={} (results={})", track_id, len(results))
        return

    # Insert track if not exists
    track_names = {i.track_id: i.track_name for i in results}
    # pyrefly: ignore[missing-attribute]
    await RRRETrack.insert(
        *[
            RRRETrack(
                track_id=dict_track_id,
                track_name=dict_track_name,
            )
            for dict_track_id, dict_track_name in track_names.items()
        ]
        # pyrefly: ignore[missing-attribute]
    ).on_conflict(target=RRRETrack.track_id, action="DO UPDATE", values=[RRRETrack.track_name])

    # Insert driver if not exists
    driver_names = {i.player_id: i.player_name for i in results}
    # pyrefly: ignore[missing-attribute]
    await RRREPlayer.insert(
        *[
            RRREPlayer(
                player_id=driver_id,
                player_name=driver_name,
            )
            for driver_id, driver_name in driver_names.items()
        ]
        # pyrefly: ignore[missing-attribute]
    ).on_conflict(target=RRREPlayer.player_id, action="DO UPDATE", values=[RRREPlayer.player_name])

    # Insert best time if not inserted in db
    # pyrefly: ignore[missing-attribute]
    await RRREBestTime.insert(
        *[
            RRREBestTime(
                player_id=i.player_id,
                track_id=track_id,
                car_class=i.car_class,
                car_name=i.car_name,
                driving_model=i.driving_model,
                datetime_driven=i.datetime_driven_parsed,
                best_time=i.best_time_parsed,
            )
            for i in results
        ]
        # pyrefly: ignore[missing-attribute]
    ).on_conflict(action="DO NOTHING")


async def main():
    while True:
        logger.info("Fetching records")
        async with httpx.AsyncClient() as client:
            for track_id in TRACK_IDS:
                data = await fetch_track_info(client, track_id=track_id)
                await update_db_data(data, track_id=track_id)
        logger.info("Fetched records")
        if settings.stage == "dev":
            return
        # Loop every hour
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
