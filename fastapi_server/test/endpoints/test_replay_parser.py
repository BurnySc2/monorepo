from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from components.replay_pack_builder.models import ParsedReplayFile
from components.replay_pack_builder.replay_parser import parse_replay
from src.main import app


@pytest.fixture
def client():
    return TestClient(app)


def _make_mock_player(name, mmr=None):
    player = MagicMock()
    player.clan_tag = ""
    player.name = name
    player.pick_race = "Terran"
    player.play_race = "Terran"
    player.is_human = True
    player._init_data = {"scaled_rating": mmr}
    return player


def _make_mock_team(players, result="Win"):
    team = MagicMock()
    team.result = result
    team.players = players
    return team


def _make_mock_replay():
    replay = MagicMock()
    player1 = _make_mock_player("Player1", mmr=1500)
    replay.teams = [_make_mock_team([player1])]
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
    return replay


@pytest.mark.asyncio
async def test_parse_replay_success():
    mock_replay = _make_mock_replay()
    with patch("sc2reader.load_replay", return_value=mock_replay):
        result = await parse_replay(BytesIO(b"fake replay data"), "abc123")
        assert isinstance(result, ParsedReplayFile)
        assert result.md5 == "abc123"
        assert result.is_ladder is True
        assert result.map_name == "Golden Wall"


@pytest.mark.asyncio
async def test_parse_replay_invalid_data():
    with patch("sc2reader.load_replay", side_effect=Exception("Invalid replay data")):
        with pytest.raises(Exception, match="Invalid replay data"):
            await parse_replay(BytesIO(b"invalid"), "abc123")


def test_parse_replay_file_success(client: TestClient):
    mock_replay = _make_mock_replay()
    fake_replay_bytes = b"fake replay file content"
    with patch("sc2reader.load_replay", return_value=mock_replay):
        response = client.post(
            "/api/parse_replay",
            files={"file": ("test.SC2Replay", fake_replay_bytes, "application/octet-stream")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["md5"] is not None


def test_parse_replay_file_invalid_replay(client: TestClient):
    invalid_file = b"not a valid replay"
    with patch("sc2reader.load_replay", side_effect=Exception("Invalid replay")):
        response = client.post(
            "/api/parse_replay",
            files={"file": ("test.SC2Replay", invalid_file, "application/octet-stream")},
        )
        assert response.status_code == 400
        assert "error" in response.json()
