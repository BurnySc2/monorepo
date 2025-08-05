import asyncio
import datetime
import os
import re

import arrow
import httpx
from pydantic import BaseModel

from models.raceroom import RRREBestTime, RRREPlayer, RRRETrack

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


def parse_player_id(url: str) -> int:
    url = url.strip("/")
    return int(url.split("/")[-1])


def parse_laptime(laptime: str) -> float:
    match: re.Match = re.match(r"(\d+)m (\d+\.\d+)s", laptime)
    minutes, seconds = match.groups()
    return int(minutes) * 60 + float(seconds)


async def fetch_track_info(client: httpx.AsyncClient, track_id: int, car_class: str = "class-5262") -> list[BestTime]:
    url = f"https://game.raceroom.com/leaderboard/listing/0?start=0&count=200&track={track_id}&car_class={car_class}"
    response = await client.get(
        url,
        # Header required to receive data as json
        headers={"x-requested-with": "XMLHttpRequest"},
    )
    if response.is_error:
        raise ValueError("Unable to fetch track and car class combination")
    data = response.json()

    data_parsed = [
        BestTime(
            player_id=parse_player_id(i["driver"]["path"]),
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
        for i in data["context"]["c"]["results"]
    ]
    return data_parsed


async def update_db_data(results: list[BestTime], track_id: int) -> None:
    # Nothing to update
    if len(results) == 0:
        return

    # Insert track if not exists
    track_names = {i.track_id: i.track_name for i in results}
    await RRRETrack.insert(
        *[
            RRRETrack(
                track_id=dict_track_id,
                track_name=dict_track_name,
            )
            for dict_track_id, dict_track_name in track_names.items()
        ]
    ).on_conflict(target=RRRETrack.track_id, action="DO UPDATE", values=[RRRETrack.track_name])

    # Insert driver if not exists
    driver_names = {i.player_id: i.player_name for i in results}
    await RRREPlayer.insert(
        *[
            RRREPlayer(
                player_id=driver_id,
                player_name=driver_name,
            )
            for driver_id, driver_name in driver_names.items()
        ]
    ).on_conflict(target=RRREPlayer.player_id, action="DO UPDATE", values=[RRREPlayer.player_name])

    # Insert best time if not inserted in db
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
    ).on_conflict(action="DO NOTHING")


async def main():
    while 1:
        async with httpx.AsyncClient() as client:
            for track_id in TRACK_IDS:
                data = await fetch_track_info(client, track_id=track_id)
                await update_db_data(data, track_id=track_id)
        if os.getenv("STAGE") == "dev":
            return
        # Loop every hour
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
