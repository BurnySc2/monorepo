from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    return TestClient(app)


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
