from pathlib import Path

from starlette.testclient import TestClient

from fastapi_server.test.base_test import BaseTest

SECOND = 22.4

REPLAY_FOLDER = Path(__file__).parent / 'replays'
REPLAYS_PATH_LIST = list(replay for replay in REPLAY_FOLDER.iterdir() if replay.suffix == '.SC2Replay')


class TestReplayParser(BaseTest):

    def test_replays(self):
        client: TestClient = self.method_client
        for replay_path in REPLAYS_PATH_LIST:
            assert replay_path.is_file()
            with replay_path.open('rb') as f:
                files = [('replay_file', f)]
                response = client.post('/parse_replay', files=files, data={'replay_tick': SECOND * 100})
            assert response.status_code == 200
            reponse_data = response.json()
            assert isinstance(reponse_data['player1'], dict)
            assert isinstance(reponse_data['player1']['name'], str)
            assert isinstance(reponse_data['player2'], dict)
            assert isinstance(reponse_data['player2']['name'], str)
            assert isinstance(reponse_data['timeline'], list)
            assert isinstance(reponse_data['timeline'][0], dict)
            assert isinstance(reponse_data['summary'], dict)
            first_summary_key = list(reponse_data['summary'].keys())[0]
            first_summary_item = reponse_data['summary'][first_summary_key]
            assert isinstance(first_summary_item, dict)
            # TODO Test more specific attributes from the dictionaries
