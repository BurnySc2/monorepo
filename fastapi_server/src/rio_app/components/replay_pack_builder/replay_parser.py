from io import BytesIO

import sc2reader
from sc2reader.resources import Replay

from rio_app.components.replay_pack_builder.models import ReplayData


async def parse_replay(data: BytesIO) -> ReplayData:
    replay: Replay = sc2reader.load_replay(data, load_level=2)
    parsed = {
        "teams": [
            {
                "result": team.result,
                "players": [
                    {
                        # May not be set on computer
                        "clan_tag": player.__dict__.get("clan_tag", ""),
                        "name": player.name,
                        "pick_race": player.pick_race,
                        "play_race": player.play_race,
                        "is_human": player.is_human,
                        # init_data is not set on computer
                        "mmr": player.__dict__.get("init_data", {}).get("scaled_rating", None),
                    }
                    for player in team.players
                ],
            }
            for team in replay.teams
        ],
        "is_ladder": replay.is_ladder,
        "is_private": replay.is_private,
        "resume_from_replay": replay.resume_from_replay,
        "played_timestamp": replay.unix_timestamp * 1000,
        "game_length_seconds": replay.length.seconds,
        "game_base_build": replay.base_build,
        "game_version": ".".join(map(str, replay.versions[1:4])),
        "game_type": replay.type,
        "map_name": replay.map_name,
        "region_short": replay.region,
        "expansion": replay.expansion,
    }
    parsed_checked = ReplayData(**parsed)
    return parsed_checked
