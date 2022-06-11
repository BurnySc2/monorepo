import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pytest
from commands.public_mmr import Sc2LadderResult


@pytest.mark.asyncio
async def test_parse_api_result():
    example_response = {
        'realm': '1',
        'region': 'EU',
        'rank': 'Grandmaster',
        'username': 'ToIsengard',
        'bnet_id': 'llllllllllll#2984',
        'race': 'Protoss',
        'mmr': 6762,
        'wins': 91,
        'losses': 47,
        'clan': 'Zorr0',
        'profile_id': 6836532,
        'alias': 'Harstem',
    }

    test_object = Sc2LadderResult(**example_response)
    result = test_object.format_result()

    correct_result = ['EU P GM', '6762', '91-47', 'ToIsengard', 'Harstem']

    assert result == correct_result
