"""Routes for RaceRoom best times data."""

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from models.raceroom import RRREBestTime, RRREPlayer, RRRETrack

raceroom_router = APIRouter()


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
    query = (
        RRREBestTime.objects(
            RRREBestTime.best_time,
            RRREBestTime.datetime_driven,
            RRREBestTime.car_name,
            RRREBestTime.driving_model,
            RRREPlayer.player_name,
            RRRETrack.track_name,
        )
        .join(RRREPlayer)
        .join(RRRETrack)
    )

    if track_id is not None:
        query = query.where(RRREBestTime.track_id == track_id)

    if start_date is not None:
        query = query.where(RRREBestTime.datetime_driven >= start_date)

    if end_date is not None:
        query = query.where(RRREBestTime.datetime_driven <= end_date)

    query = query.order_by(RRREBestTime.datetime_driven)

    best_times = await query
    return JSONResponse(
        [
            {
                "date": bt.datetime_driven.isoformat() if bt.datetime_driven else None,
                "driver_name": bt.player_name,
                "car_name": bt.car_name,
                "driving_model": bt.driving_model,
                "track_name": bt.track_name,
                "best_time": bt.best_time,
            }
            for bt in best_times
        ]
    )
