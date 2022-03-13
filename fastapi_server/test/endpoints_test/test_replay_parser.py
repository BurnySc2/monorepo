from pathlib import Path

from starlette.testclient import TestClient

from fastapi_server.test.base_test import BaseTest

TEST_REPLAY = Path(__file__).parent / 'replays' / 'TvZ Standard Bio.SC2Replay'


class TestReplayParser(BaseTest):

    def test_parse_single_replay(self):
        assert TEST_REPLAY.is_file()
        client: TestClient = self.method_client
        with TEST_REPLAY.open('rb') as f:
            files = [('replay_file', f)]
            second = 22.4
            response = client.post('/parse_replay', files=files, data={'replay_tick': second * 10})
        assert response.status_code == 200
        reponse_data = response.json()
        assert reponse_data['player1']['name'] == 'BuRny'
