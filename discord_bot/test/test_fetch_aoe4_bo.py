from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientSession
from hypothesis import example, given, settings
from hypothesis import strategies as st
from hypothesis.strategies import DataObject
from loguru import logger

from commands.public_fetch_aoe4 import (
    ALLOWED_RACES,
    Action,
    BuildOrderItem,
    BuildOrderParserOptions,
    Condition,
    FinishedActions,
    GamePlayerData,
    GameResult,
    PlayerOfTeam,
    PlayerOfTeamEntry,
    PlayerSearchResult,
    public_analyse_aoe4_game,
    public_fetch_aoe4_bo,
    public_search_aoe4_players,
)

logger.remove()

ALLOWED_ACTION_ENUM_VALUES: set[str] = {
    'v', 'villager', 'villagers', 'tc', 'tcs', 'towncenter', 'towncenters', 'age2', 'feudal', 'age3', 'castle', 'age4',
    'imp', 'imperial', 'wb', 'wheel', 'wheelbarrow'
}


@given(st.sampled_from(list(ALLOWED_ACTION_ENUM_VALUES)))
def test_action_enum_success(test_input: str):
    parsed = Action.parse_action(test_input)
    assert isinstance(parsed, Action)


@given(st.text())
def test_action_enum_failure(test_input: str):
    if test_input not in ALLOWED_ACTION_ENUM_VALUES:
        with pytest.raises(ValueError):
            _parsed = Action.parse_action(test_input)


@given(
    optional_count=st.from_regex(r'(\d+)?', fullmatch=True),
    action=st.from_regex(r'(\w+)', fullmatch=True),
    operator=st.from_regex('(<)?', fullmatch=True),
    duration=st.from_regex(r'(\d+)?', fullmatch=True),
    duration_suffix=st.from_regex('(s|m)?', fullmatch=True),
)
@example('4', 'towncenters', '<', '600', '')
@example('4', 'towncenters', '<', '600', 's')
@example('4', 'towncenters', '<', '10', 'm')
@example('1', 'wheelbarrow', '', '', '')
@example('', 'wheelbarrow', '', '', '')
@example('60', 'villagers', '<', '600', 's')
def test_condition_enum(optional_count: str, action: str, operator: str, duration: str, duration_suffix: str):
    input_string = f'{optional_count}{action}{operator}{duration}{duration_suffix}'
    if action not in ALLOWED_ACTION_ENUM_VALUES:
        with pytest.raises(ValueError):
            _parsed = Condition.from_string(input_string)
        return
    parsed = Condition.from_string(input_string)
    assert isinstance(parsed, Condition)


@pytest.mark.asyncio
@given(
    message_text=st.from_regex(r'\w+', fullmatch=True),
    player_search_results=st.lists(st.builds(PlayerSearchResult)),
)
async def test_public_search_aoe4_players(message_text: str, player_search_results: list[PlayerSearchResult]):
    with patch.object(
        ClientSession, 'get',
        AsyncMock(
            return_value=AsyncMock(
                ok=True,
                json=AsyncMock(
                    return_value={
                        'players': [player_search_result.dict() for player_search_result in player_search_results]
                    }
                ),
            )
        )
    ):
        # pyre-fixme[6]
        result = await public_search_aoe4_players(None, None, message_text)
        if len(player_search_results) == 0:
            assert result == 'Could not find any player with this name.'
            return
        player_search_results.sort(key=lambda player: player.last_game_at_arrow, reverse=True)
        result_string = '\n'.join(
            [
                f'Last game was {player.last_game_at_arrow.humanize()}, {player.name} '
                f'<https://aoe4world.com/players/{player.profile_id}>'
                # Only list the first 10 players
                for player in player_search_results[:10]
            ]
        )
        assert result == result_string


@pytest.mark.asyncio
@given(
    data=st.data(),
    player_profile_id=st.integers(min_value=1),
    game_id=st.integers(min_value=1),
)
async def test_public_analyse_aoe4_game(data: DataObject, player_profile_id: int, game_id: int):
    game_players_data = data.draw(
        st.lists(
            st.builds(
                GamePlayerData,
                profile_id=st.sampled_from([0, player_profile_id]),
                actions=st.builds(FinishedActions),
                build_order=st.lists(st.from_type(BuildOrderItem), max_size=0)
            )
        )
    )
    message_text = f'https://aoe4world.com/players/{player_profile_id}/games/{game_id}'

    with patch.object(
        ClientSession, 'get',
        AsyncMock(
            return_value=AsyncMock(
                ok=True,
                json=AsyncMock(
                    return_value={'players': [game_player_data.dict() for game_player_data in game_players_data]}
                )
            )
        )
    ):
        # pyre-fixme[6]
        result = await public_analyse_aoe4_game(None, None, message_text)
        found_game_player_data: GamePlayerData | None = next(
            (i for i in game_players_data if i.profile_id == player_profile_id), None
        )
        if found_game_player_data is None:
            assert result == 'Game was not found. Is the link valid?'
            return
        result_string = f'Analysis of game <{message_text}>\n{found_game_player_data.to_discord_message()}'
        assert result == result_string


@pytest.mark.asyncio
@settings(deadline=2000)
@given(
    data=st.data(),
    amount_of_games_per_page=st.integers(min_value=1, max_value=10),
    amount_of_players_per_team=st.integers(min_value=1, max_value=4),
    player_race=st.sampled_from(list(ALLOWED_RACES)),
    player_profile_id=st.integers(min_value=1),
    villagers_built=st.integers(min_value=1, max_value=100),
    villagers_required=st.integers(min_value=1, max_value=100),
)
async def test_public_fetch_aoe4_bo_match_villager_condition(
    data: DataObject,
    amount_of_games_per_page: int,
    amount_of_players_per_team: int,
    player_race: str,
    player_profile_id: int,
    villagers_built: int,
    villagers_required: int,
):
    AMOUNT_OF_PAGES = 20
    AMOUNT_OF_TEAMS = 2
    TOTAL_BUILD_ORDERS = AMOUNT_OF_PAGES * amount_of_games_per_page * AMOUNT_OF_TEAMS * amount_of_players_per_team

    build_order_item = data.draw(
        st.builds(
            BuildOrderItem,
            icon=st.just('icons/races/common/units/villager'),
            finished=st.just([0] * villagers_built),
            constructed=st.just([]),
        )
    ).dict()
    build_order_parser_input = data.draw(
        st.builds(
            BuildOrderParserOptions,
            # Condition matching the build order above
            condition=st.just(f'{villagers_required}villagers<1s'),
            profile_id=st.just(player_profile_id),
            race=st.just(player_race),
        )
    )
    message_text = build_order_parser_input.to_string

    with patch.object(
        ClientSession,
        'get',
        AsyncMock(
            side_effect=[
                # Fetch profile
                AsyncMock(
                    ok=True,
                    json=AsyncMock(
                        return_value=data.draw(
                            st.builds(
                                PlayerSearchResult,
                                # Required for finding profile
                                profile_id=st.just(player_profile_id),
                            )
                        ).dict()
                    ),
                ),
            ] + AMOUNT_OF_PAGES * [
                # Fetch games matching the profile, will be called 20 times (20 pages) because profile id was submitted
                AsyncMock(
                    ok=True,
                    json=AsyncMock(
                        return_value={
                            'games': data.draw(
                                st.lists(
                                    st.builds(
                                        GameResult,
                                        # Will only take games from the latest patch
                                        patch=st.just(0),
                                        # Will filter out ongoing games
                                        ongoing=st.just(False),
                                        # Will filter out games shorter than 10 mins
                                        duration=st.just(601),
                                        # Required for sorting
                                        started_at=st.just('2000-01-01'),
                                        teams=st.lists(
                                            st.lists(
                                                st.builds(
                                                    PlayerOfTeamEntry,
                                                    player=st.builds(
                                                        PlayerOfTeam,
                                                        profile_id=st.just(player_profile_id),
                                                        civilization=st.just(player_race)
                                                    )
                                                ),
                                                min_size=amount_of_players_per_team,
                                                max_size=amount_of_players_per_team,
                                            ),
                                            min_size=AMOUNT_OF_TEAMS,
                                            max_size=AMOUNT_OF_TEAMS
                                        )
                                    ),
                                    min_size=amount_of_games_per_page,
                                    max_size=amount_of_games_per_page
                                )
                            )
                        }
                    )
                )
            ] + TOTAL_BUILD_ORDERS * [
                # Fetch build orders of each player from the game
                AsyncMock(
                    ok=True,
                    json=AsyncMock(
                        return_value={
                            'players': data.draw(
                                st.lists(
                                    st.builds(
                                        GamePlayerData,
                                        profile_id=st.just(player_profile_id),
                                        actions=st.builds(FinishedActions),
                                        build_order=st.just([build_order_item])
                                    ),
                                    min_size=1,
                                    max_size=1,
                                )
                            )
                        }
                    )
                ),
            ]
        )
    ) as get_mock:
        # pyre-fixme[6]
        result = await public_fetch_aoe4_bo(None, None, message_text)
        assert get_mock.call_count == TOTAL_BUILD_ORDERS + AMOUNT_OF_PAGES + 1
        if villagers_built >= villagers_required:
            assert result.startswith(f'Found {TOTAL_BUILD_ORDERS} games that match this request\n')
        else:
            assert result == f'Parsed {TOTAL_BUILD_ORDERS} games. No games match this request'


# TODO Test condition with feudal, castle, imperial, wheelbarrow
# TODO Return no results when race mismatch
