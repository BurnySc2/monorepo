import sys
from pathlib import Path

try:
    sys.path.append(str(Path(__file__).parents[2]))
except IndexError:
    pass

import pytest

from discord_bot.commands.public_mmr import Sc2LadderResult


@pytest.mark.asyncio
async def test_parse_api_result():
    example_response = {
        'leagueMax': 6,
        'ratingMax': 6820,
        'totalGamesPlayed': 8088,
        'previousStats': {
            'rating': 6599,
            'gamesPlayed': 68,
            'rank': 1653
        },
        'currentStats': {
            'rating': 6632,
            'gamesPlayed': 32,
            'rank': 69
        },
        'members': {
            'protossGamesPlayed': 8088,
            'character': {
                'realm': 1,
                'name': 'Harstem#1',
                'id': 677353,
                'accountId': 677353,
                'region': 'EU',
                'battlenetId': 7100931,
                'clanId': 4535
            },
            'account': {
                'battleTag': 'Harstem#21371',
                'id': 677353,
                'partition': 'GLOBAL',
                'hidden': None
            },
            'clan': {
                'tag': 'RBLN',
                'id': 4535,
                'region': 'EU',
                'name': 'Shopify Rebellion',
                'members': 4,
                'activeMembers': 4,
                'avgRating': 6111,
                'avgLeagueType': 5,
                'games': 852
            },
            'proNickname': 'Harstem',
            'proTeam': 'ShopifyRebels'
        }
    }

    test_object = Sc2LadderResult.from_api_result(example_response)
    result = test_object.format_result()

    correct_result = ['EU P', '6632', '32', '[RBLN] Harstem']

    assert result == correct_result
