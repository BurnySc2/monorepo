"""Offline tests for the RaceRoom leaderboard worker (no DB, no network)."""

import httpx
import pytest

from workers.raceroom_fetch_records import fetch_track_info, parse_player_id

_AVATAR_BASE = "https://game.raceroomracing.com/game/user_avatar"


@pytest.mark.parametrize(
    ("driver", "want"),
    [
        ({"avatar": f"{_AVATAR_BASE}/1233502", "path": "/users/Fogino"}, 1233502),
        ({"avatar": f"{_AVATAR_BASE}/1233502?size=1"}, 1233502),
        ({"avatar": f"{_AVATAR_BASE}/1233502#x"}, 1233502),
        ({"avatar": f"{_AVATAR_BASE}/12abc"}, None),
        ({"avatar": f"{_AVATAR_BASE}/"}, None),
        ({"path": "/users/Fogino"}, None),
        ({"path": "/driver/12345"}, None),
        ({}, None),
    ],
)
def test_parse_player_id(driver: dict, want: int | None) -> None:
    """Only the numeric avatar URL yields an id; missing ids return None."""
    assert parse_player_id(driver) == want


def _result(*, name: str, avatar: str | None, path: str) -> dict:
    driver: dict = {"name": name, "path": path}
    if avatar is not None:
        driver["avatar"] = avatar
    return {
        "driver": driver,
        "track": {"name": "Oschersleben"},
        "car_class": {"car": {"class-name": "class-5262", "name": "BMW M4"}},
        "driving_model": "GetReal",
        "date_time": "2026-01-02T03:04:05Z",
        "laptime": "1m 23.456s",
    }


async def test_fetch_track_info_skips_result_without_player_id() -> None:
    """A result without a parsable avatar id is skipped instead of crashing."""
    payload = {
        "context": {
            "c": {
                "results": [
                    _result(name="Fogino", avatar=f"{_AVATAR_BASE}/1233502", path="/users/Fogino"),
                    _result(name="NoAvatar", avatar=None, path="/users/Fogino"),
                ]
            }
        }
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        data = await fetch_track_info(client, track_id=12506)

    assert len(data) == 1
    assert data[0].player_id == 1233502
    assert data[0].player_name == "Fogino"
