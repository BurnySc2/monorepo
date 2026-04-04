"""Tests for RaceRoom endpoints."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from piccolo.table import create_db_tables, drop_db_tables
from piccolo.utils.sync import run_sync

from src.main import app
from src.models.raceroom import RRREBestTime, RRREPlayer, RRRETrack

RACEROOM_TABLES = [RRREPlayer, RRRETrack, RRREBestTime]


@pytest.fixture(scope="function")
def test_client_raceroom() -> TestClient:
    """Test client with fresh RaceRoom database tables."""
    run_sync(create_db_tables(*RACEROOM_TABLES, if_not_exists=True))
    try:
        with TestClient(app=app) as client:
            yield client
    finally:
        run_sync(drop_db_tables(*RACEROOM_TABLES))


def test_get_tracks_empty(test_client_raceroom: TestClient) -> None:
    """GET /api/raceroom/tracks returns empty list initially."""
    response = test_client_raceroom.get("/api/raceroom/tracks")
    assert response.status_code == 200
    assert response.json() == []


def test_get_tracks_with_data(test_client_raceroom: TestClient) -> None:
    """GET /api/raceroom/tracks returns tracks sorted by track_name."""
    RRRETrack(
        track_id=1,
        track_name="Zandvoort",
    ).save().run_sync()
    RRRETrack(
        track_id=2,
        track_name="Silverstone",
    ).save().run_sync()
    RRRETrack(
        track_id=3,
        track_name="Monza",
    ).save().run_sync()

    response = test_client_raceroom.get("/api/raceroom/tracks")
    assert response.status_code == 200
    tracks = response.json()
    assert len(tracks) == 3
    assert tracks[0] == {"id": 3, "name": "Monza"}
    assert tracks[1] == {"id": 2, "name": "Silverstone"}
    assert tracks[2] == {"id": 1, "name": "Zandvoort"}


def test_get_times_no_filters(test_client_raceroom: TestClient) -> None:
    """GET /api/raceroom/times with no filters returns all times ordered by datetime_driven."""
    RRREPlayer(player_id=1, player_name="Driver1").save().run_sync()
    RRRETrack(track_id=1, track_name="Track1").save().run_sync()
    RRREBestTime(
        player_id=1,
        track_id=1,
        car_name="Car A",
        driving_model="Amateur",
        datetime_driven=datetime(2024, 1, 1, 12, 0, 0),
        best_time=90.5,
    ).save().run_sync()
    RRREBestTime(
        player_id=1,
        track_id=1,
        car_name="Car B",
        driving_model="Get Real",
        datetime_driven=datetime(2024, 1, 2, 12, 0, 0),
        best_time=85.2,
    ).save().run_sync()

    response = test_client_raceroom.get("/api/raceroom/times")
    assert response.status_code == 200
    times = response.json()
    assert len(times) == 2
    assert times[0]["best_time"] == 90.5
    assert times[1]["best_time"] == 85.2


def test_get_times_filter_by_track_id(test_client_raceroom: TestClient) -> None:
    """GET /api/raceroom/times with track_id filter returns only that track's times."""
    RRREPlayer(player_id=1, player_name="Driver1").save().run_sync()
    RRRETrack(track_id=1, track_name="Track1").save().run_sync()
    RRRETrack(track_id=2, track_name="Track2").save().run_sync()
    RRREBestTime(
        player_id=1,
        track_id=1,
        car_name="Car A",
        driving_model="Amateur",
        datetime_driven=datetime(2024, 1, 1, 12, 0, 0),
        best_time=90.5,
    ).save().run_sync()
    RRREBestTime(
        player_id=1,
        track_id=2,
        car_name="Car B",
        driving_model="Get Real",
        datetime_driven=datetime(2024, 1, 2, 12, 0, 0),
        best_time=85.2,
    ).save().run_sync()

    response = test_client_raceroom.get("/api/raceroom/times", params={"track_id": 1})
    assert response.status_code == 200
    times = response.json()
    assert len(times) == 1
    assert times[0]["track_name"] == "Track1"


def test_get_times_filter_by_start_date(test_client_raceroom: TestClient) -> None:
    """GET /api/raceroom/times with start_date filter excludes older times."""
    RRREPlayer(player_id=1, player_name="Driver1").save().run_sync()
    RRRETrack(track_id=1, track_name="Track1").save().run_sync()
    RRREBestTime(
        player_id=1,
        track_id=1,
        car_name="Car A",
        driving_model="Amateur",
        datetime_driven=datetime(2024, 1, 1, 12, 0, 0),
        best_time=90.5,
    ).save().run_sync()
    RRREBestTime(
        player_id=1,
        track_id=1,
        car_name="Car B",
        driving_model="Get Real",
        datetime_driven=datetime(2024, 1, 15, 12, 0, 0),
        best_time=85.2,
    ).save().run_sync()
    RRREBestTime(
        player_id=1,
        track_id=1,
        car_name="Car C",
        driving_model="Novice",
        datetime_driven=datetime(2024, 2, 1, 12, 0, 0),
        best_time=80.0,
    ).save().run_sync()

    response = test_client_raceroom.get("/api/raceroom/times", params={"start_date": "2024-01-10"})
    assert response.status_code == 200
    times = response.json()
    assert len(times) == 2
    assert times[0]["best_time"] == 85.2
    assert times[1]["best_time"] == 80.0


def test_get_times_filter_by_end_date(test_client_raceroom: TestClient) -> None:
    """GET /api/raceroom/times with end_date filter excludes newer times."""
    RRREPlayer(player_id=1, player_name="Driver1").save().run_sync()
    RRRETrack(track_id=1, track_name="Track1").save().run_sync()
    RRREBestTime(
        player_id=1,
        track_id=1,
        car_name="Car A",
        driving_model="Amateur",
        datetime_driven=datetime(2024, 1, 1, 12, 0, 0),
        best_time=90.5,
    ).save().run_sync()
    RRREBestTime(
        player_id=1,
        track_id=1,
        car_name="Car B",
        driving_model="Get Real",
        datetime_driven=datetime(2024, 1, 15, 12, 0, 0),
        best_time=85.2,
    ).save().run_sync()
    RRREBestTime(
        player_id=1,
        track_id=1,
        car_name="Car C",
        driving_model="Novice",
        datetime_driven=datetime(2024, 2, 1, 12, 0, 0),
        best_time=80.0,
    ).save().run_sync()

    response = test_client_raceroom.get("/api/raceroom/times", params={"end_date": "2024-01-20"})
    assert response.status_code == 200
    times = response.json()
    assert len(times) == 2
    assert times[0]["best_time"] == 90.5
    assert times[1]["best_time"] == 85.2


def test_get_times_combined_filters(test_client_raceroom: TestClient) -> None:
    """GET /api/raceroom/times with combined filters applies all filters."""
    RRREPlayer(player_id=1, player_name="Driver1").save().run_sync()
    RRRETrack(track_id=1, track_name="Track1").save().run_sync()
    RRRETrack(track_id=2, track_name="Track2").save().run_sync()
    RRREBestTime(
        player_id=1,
        track_id=1,
        car_name="Car A",
        driving_model="Amateur",
        datetime_driven=datetime(2024, 1, 1, 12, 0, 0),
        best_time=90.5,
    ).save().run_sync()
    RRREBestTime(
        player_id=1,
        track_id=1,
        car_name="Car B",
        driving_model="Get Real",
        datetime_driven=datetime(2024, 1, 15, 12, 0, 0),
        best_time=85.2,
    ).save().run_sync()
    RRREBestTime(
        player_id=1,
        track_id=2,
        car_name="Car C",
        driving_model="Novice",
        datetime_driven=datetime(2024, 1, 20, 12, 0, 0),
        best_time=80.0,
    ).save().run_sync()

    response = test_client_raceroom.get(
        "/api/raceroom/times",
        params={"track_id": 1, "start_date": "2024-01-10", "end_date": "2024-01-16"},
    )
    assert response.status_code == 200
    times = response.json()
    assert len(times) == 1
    assert times[0]["car_name"] == "Car B"
    assert times[0]["track_name"] == "Track1"


def test_get_times_no_results(test_client_raceroom: TestClient) -> None:
    """GET /api/raceroom/times returns empty list when no matches."""
    RRREPlayer(player_id=1, player_name="Driver1").save().run_sync()
    RRRETrack(track_id=1, track_name="Track1").save().run_sync()
    RRREBestTime(
        player_id=1,
        track_id=1,
        car_name="Car A",
        driving_model="Amateur",
        datetime_driven=datetime(2024, 1, 1, 12, 0, 0),
        best_time=90.5,
    ).save().run_sync()

    response = test_client_raceroom.get("/api/raceroom/times", params={"track_id": 999})
    assert response.status_code == 200
    assert response.json() == []
