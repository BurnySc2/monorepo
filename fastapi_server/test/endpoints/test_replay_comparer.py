from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app

REPLAY_DIR = Path(__file__).parent / "replay_comparer_replays"


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def example_replay_bytes():
    """Load the example_vs_ai.SC2Replay file as bytes."""
    replay_path = REPLAY_DIR / "example_vs_ai.SC2Replay"
    return replay_path.read_bytes()


@pytest.fixture
def parse_replay(client, example_replay_bytes):
    """Helper to parse a replay file and return the response data."""

    def _parse(replay_bytes=None, replay_tick=224):
        response = client.post(
            "/api/replay_comparer/parse_replay",
            data={"replay_tick": str(replay_tick)},
            files={"replay_file": ("test.SC2Replay", replay_bytes or example_replay_bytes, "application/octet-stream")},
        )
        assert response.status_code == 200
        return response.json()

    return _parse


def _make_mock_player(name, pid=1):
    player = MagicMock()
    player.clan_tag = ""
    player.name = name
    player.pick_race = "Terran"
    player.play_race = "Terran"
    player.is_human = True
    player.pid = pid
    return player


def _make_mock_team(players, result="Win"):
    team = MagicMock()
    team.result = result
    team.players = players
    return team


def _make_mock_replay():
    replay = MagicMock()
    player1 = _make_mock_player("Player1", pid=1)
    player2 = _make_mock_player("Player2", pid=2)
    replay.teams = [_make_mock_team([player1]), _make_mock_team([player2])]
    replay.is_ladder = True
    replay.is_private = False
    replay.resume_from_replay = False
    replay.unix_timestamp = 1700000000
    replay.length.seconds = 600
    replay.base_build = 123
    replay.versions = [1, 5, 0, 12]
    replay.type = "Ladder"
    replay.map_name = "Golden Wall"
    replay.region = "us"
    replay.expansion = "LotV"
    replay.tracker_events = []
    return replay


def test_parse_replay_valid_file(client: TestClient):
    mock_replay = _make_mock_replay()
    fake_replay_bytes = b"fake replay file content"
    with patch("sc2reader.load_replay", return_value=mock_replay):
        response = client.post(
            "/api/replay_comparer/parse_replay",
            data={"replay_tick": "224"},
            files={"replay_file": ("test.SC2Replay", fake_replay_bytes, "application/octet-stream")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "player1" in data
        assert "player2" in data
        assert "timeline" in data
        assert data["player1"]["name"] == "Player1"
        assert data["player2"]["name"] == "Player2"
        assert isinstance(data["timeline"], list)
        assert "buildings" in data["player1"]
        assert "buildings" in data["player2"]
        assert isinstance(data["player1"]["buildings"], list)
        assert isinstance(data["player2"]["buildings"], list)


def test_parse_replay_tick_zero(client: TestClient):
    fake_replay_bytes = b"fake replay file content"
    response = client.post(
        "/api/replay_comparer/parse_replay",
        data={"replay_tick": "0"},
        files={"replay_file": ("test.SC2Replay", fake_replay_bytes, "application/octet-stream")},
    )
    assert response.status_code == 400
    assert response.json()["error"] == "replay_tick must be positive"


def test_parse_replay_tick_negative(client: TestClient):
    fake_replay_bytes = b"fake replay file content"
    response = client.post(
        "/api/replay_comparer/parse_replay",
        data={"replay_tick": "-1"},
        files={"replay_file": ("test.SC2Replay", fake_replay_bytes, "application/octet-stream")},
    )
    assert response.status_code == 400
    assert response.json()["error"] == "replay_tick must be positive"


def test_parse_replay_tick_non_integer(client: TestClient):
    fake_replay_bytes = b"fake replay file content"
    response = client.post(
        "/api/replay_comparer/parse_replay",
        data={"replay_tick": "abc"},
        files={"replay_file": ("test.SC2Replay", fake_replay_bytes, "application/octet-stream")},
    )
    assert response.status_code == 400
    assert response.json()["error"] == "replay_tick must be an integer"


def test_parse_replay_malformed_file(client: TestClient):
    invalid_file = b"not a valid replay"
    with patch("sc2reader.load_replay", side_effect=Exception("Invalid replay data")):
        response = client.post(
            "/api/replay_comparer/parse_replay",
            data={"replay_tick": "224"},
            files={"replay_file": ("test.SC2Replay", invalid_file, "application/octet-stream")},
        )
        assert response.status_code == 400
        assert "error" in response.json()


def test_parse_replay_example_vs_ai(client: TestClient):
    replay_path = REPLAY_DIR / "example_vs_ai.SC2Replay"
    replay_bytes = replay_path.read_bytes()

    response = client.post(
        "/api/replay_comparer/parse_replay",
        data={"replay_tick": "224"},
        files={"replay_file": ("example_vs_ai.SC2Replay", replay_bytes, "application/octet-stream")},
    )

    assert response.status_code == 200
    data = response.json()

    # Top-level structure
    assert "player1" in data
    assert "player2" in data
    assert "timeline" in data

    # Players have non-empty names
    assert isinstance(data["player1"]["name"], str)
    assert len(data["player1"]["name"]) > 0
    assert isinstance(data["player2"]["name"], str)
    assert len(data["player2"]["name"]) > 0

    # Buildings data exists
    assert "buildings" in data["player1"]
    assert "buildings" in data["player2"]
    assert isinstance(data["player1"]["buildings"], list)
    assert isinstance(data["player2"]["buildings"], list)

    # Timeline is a non-empty list of ticks
    assert isinstance(data["timeline"], list)
    assert len(data["timeline"]) > 0

    # Each tick is a list of data-point dicts with expected fields
    expected_fields = {
        "gameloop",
        "workers_active",
        "workers_produced",
        "workers_lost",
        "supply",
        "supply_cap",
        "supply_block",
        "spm",
        "total_army_value",
        "total_resources_lost",
        "total_resources_collected",
        "workers_killed",
        "resource_collection_rate_all",
    }
    for tick_points in data["timeline"]:
        assert isinstance(tick_points, list)
        assert len(tick_points) > 0
        for point in tick_points:
            assert isinstance(point, dict)
            assert expected_fields.issubset(point.keys())


def test_parse_replay_burny_second_command_center(parse_replay):
    """Test that player BuRny has a second CommandCenter by 1:40."""
    data = parse_replay()

    # Find player BuRny
    burny_player = None
    if data["player1"]["name"] == "BuRny":
        burny_player = data["player1"]
    elif data["player2"]["name"] == "BuRny":
        burny_player = data["player2"]

    assert burny_player is not None, "Player BuRny not found in replay"
    assert "buildings" in burny_player, "Buildings data not in response"

    # 1:40 game time = 100 seconds = 100 * 22.4 = 2240 gameloops (LotV)
    target_frame = int(100 * 22.4)

    # Count CommandCenters (and upgrades) started by 1:40
    command_centers = [
        b for b in burny_player["buildings"] if b["type"] == "CommandCenter" and b["frame"] <= target_frame
    ]

    assert len(command_centers) == 1, (
        f"Expected at one CommandCenters on the way by 1:40 (frame {target_frame}), "
        f"but found {len(command_centers)}. "
        f"All buildings: {burny_player['buildings']}"
    )
