from dataclasses import dataclass
from typing import Dict, List, Union

from fastapi import File, Form, UploadFile
from fastapi.routing import APIRouter
from zephyrus_sc2_parser import parse_replay
from zephyrus_sc2_parser.dataclasses import Resource
from zephyrus_sc2_parser.game import Player

replay_parser_router = APIRouter()


@dataclass
class RequestBody:
    replay_tick: int = 112


# pylint: disable=R0902
@dataclass
class ParserPlayer:
    name: str
    race: str
    supply_block: int
    army_value: Dict[Resource, List[int]]
    collection_rate: Dict[Resource, List[int]]
    unspent_resources: Dict[Resource, List[int]]
    upgrades: List[Dict[str, Union[str, int]]]
    queues: List[dict]

    @staticmethod
    def from_replay_object(player_object: Player):
        return ParserPlayer(
            name=player_object.name,
            race=player_object.race,
            supply_block=player_object.supply_block,
            army_value=player_object.army_value,
            collection_rate=player_object.collection_rate,
            unspent_resources=player_object.unspent_resources,
            upgrades=[
                {
                    'name': upgrade.name,
                    'completed_at': upgrade.completed_at,
                } for upgrade in player_object.upgrades
            ],
            queues=[
                {
                    'gameloop': queue['gameloop'],
                    'supply_blocked': queue['supply_blocked'],
                    'queues': [
                        {
                            'structure_name': structure.name,
                            'structure_queue': [
                                {
                                    'name': structure_queue_item.name,
                                } for structure_queue_item in structure_queue
                            ]
                        } for structure, structure_queue in queue['queues'].items()
                    ]
                } for queue in player_object.queues
            ],
        )


@replay_parser_router.post('/parse_replay')
async def parse_replay_endpoint(replay_tick: float = Form(112), replay_file: UploadFile = File(...)):
    # async def parse_replay_endpoint(replay_tick: float = Form(112)):
    replay_tick = max(20, int(round(replay_tick)))
    # https://fastapi.tiangolo.com/tutorial/request-files/#uploadfile
    players, timeline, _engagements, summary, metadata = parse_replay(
        replay_file.file, local=True, tick=replay_tick, network=False
    )

    player1 = ParserPlayer.from_replay_object(players[1])
    player2 = ParserPlayer.from_replay_object(players[2])

    return {
        'metadata': metadata,
        'summary': summary,
        'timeline': timeline,
        'player1': player1,
        'player2': player2,
    }
