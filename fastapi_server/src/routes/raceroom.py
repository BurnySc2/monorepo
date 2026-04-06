"""Routes for RaceRoom best times data."""

from pathlib import Path

import arrow
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from models.raceroom import RRREBestTime, RRRETrack

raceroom_router = APIRouter()

_queries_directory = Path(__file__).parent.parent / "queries"
_query_get_times = (_queries_directory / "raceroom_get_times.sql").read_text()


@raceroom_router.get("/api/raceroom/tracks")
async def get_tracks() -> JSONResponse:
    """Get all available tracks."""
    tracks = await RRRETrack.objects().order_by(RRRETrack.track_name)
    return JSONResponse([{"id": track.track_id, "name": track.track_name} for track in tracks])


@raceroom_router.get("/api/raceroom/times")
async def get_times(
    track_id: int | None = Query(default=None, description="Filter by track ID"),
    start_date: str | None = Query(default=None, description="Filter by start date (ISO format)"),
    end_date: str | None = Query(default=None, description="Filter by end date (ISO format)"),
) -> JSONResponse:
    """Get best times with optional filters."""
    rows: list[dict] = await RRREBestTime.raw(
        _query_get_times,
        track_id if track_id is not None else None,
        arrow.get(start_date).naive if start_date is not None else None,
        arrow.get(end_date).naive if end_date is not None else None,
    )
    return JSONResponse(
        [
            {
                "date": row["datetime_driven"].isoformat() if row["datetime_driven"] else None,
                "driver_name": row["player_name"],
                "car_name": row["car_name"],
                "driving_model": row["driving_model"],
                "track_name": row["track_name"],
                "best_time": row["best_time"],
            }
            for row in rows
        ]
    )
