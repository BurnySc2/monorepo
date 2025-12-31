from uuid import uuid4

import arrow
import rio

from rio_app.components.replay_pack_builder.models import ParsedReplayFile


class FilterSettings(rio.UserSettings):
    filter_enabled: bool = True
    game_matchmaking: bool = True
    game_custom: bool = True
    game_coop: bool = True
    game_arcade: bool = True
    game_include_games_with_ai: bool = False
    game_include_games_resumed_from_replay: bool = False
    expansion_wol: bool = True
    expansion_hots: bool = True
    expansion_lotv: bool = True
    server_americas: bool = True
    server_europe: bool = True
    server_asia: bool = True
    # Unable do store as date (can't convert to JSON bug?)
    date_played_min: float = arrow.get("2010-01-01").timestamp()
    date_played_max: float = arrow.utcnow().timestamp()
    game_duration_min: int = 0
    game_duration_max: int = 9999
    player_count_min: int = 2
    player_count_max: int = 2
    average_mmr_min: int = 0
    average_mmr_max: int = 9999
    matchup_pvp: bool = True
    matchup_pvt: bool = True
    matchup_pvz: bool = True
    matchup_tvt: bool = True
    matchup_tvz: bool = True
    matchup_zvz: bool = True
    player_name_must_include: str = ""
    player_name_must_exclude: str = ""
    map_name_must_include: str = ""
    map_name_must_exclude: str = ""

    # Identifier to store replays
    user_id: str = str(uuid4())

    async def replay_passes_filter(self, replay: ParsedReplayFile) -> bool:
        if not self.filter_enabled:
            return True
        if not self.game_matchmaking and replay.is_ladder:
            return False
        if not self.game_custom and replay.is_private:
            return False
        # TODO Coop and arcade replays
        has_computers = any(not player.is_human for team in replay.teams for player in team.players)
        if not self.game_include_games_with_ai and has_computers:
            return False
        if not self.game_include_games_resumed_from_replay and replay.resume_from_replay:
            return False
        # Expansion
        if any(
            [
                not self.expansion_wol and replay.expansion == "WoL",
                not self.expansion_hots and replay.expansion == "HotS",
                not self.expansion_lotv and replay.expansion == "LotV",
            ]
        ):
            return False
        # Server
        if not self.server_americas and replay.region_short == "us":
            return False
        if not self.server_europe and replay.region_short == "eu":
            return False
        if not self.server_asia and replay.region_short == "kr":
            return False

        # Date played filter
        game_date = arrow.get(replay.played_timestamp).timestamp()
        if not (self.date_played_min <= game_date <= self.date_played_max):
            return False

        # Game duration filter
        if not (self.game_duration_min <= replay.game_length_seconds <= self.game_duration_max):
            return False

        # Average mmr filter
        average_mmr = sum(player.mmr for team in replay.teams for player in team.players if player.mmr is not None)
        if not (self.average_mmr_min <= average_mmr <= self.average_mmr_max):
            return False

        # Player count filter
        teams_count = len(replay.teams)
        players_count = sum(len(team.players) for team in replay.teams)

        # Matchup filter
        if teams_count == 2 and players_count == 2:
            players = [replay.teams[0].players[0], replay.teams[1].players[0]]
            player_races = "v".join(p.play_race[0] for p in sorted(players, key=lambda i: i.play_race))
            if not self.matchup_pvp and player_races == "PvP":
                return False
            if not self.matchup_pvt and player_races == "PvT":
                return False
            if not self.matchup_pvz and player_races == "PvZ":
                return False
            if not self.matchup_tvt and player_races == "TvT":
                return False
            if not self.matchup_tvz and player_races == "TvZ":
                return False
            if not self.matchup_zvz and player_races == "ZvZ":
                return False

        # Player name include / exclude filter
        all_player_names = [player.name.lower() for team in replay.teams for player in team.players]

        players_must_include = [
            i.strip().lower() for i in self.player_name_must_include.strip().split(",") if i.strip()
        ]
        map_name_matches_include = False
        if players_must_include:
            for player_name in all_player_names:
                for search_string in players_must_include:
                    if search_string in player_name:
                        map_name_matches_include = True
            if not map_name_matches_include:
                return False

        players_must_exclude = [
            i.strip().lower() for i in self.player_name_must_exclude.strip().split(",") if i.strip()
        ]
        map_name_matches_exclude = False
        if players_must_exclude:
            for player_name in all_player_names:
                for search_string in players_must_exclude:
                    if search_string in player_name:
                        map_name_matches_exclude = True
            if map_name_matches_exclude:
                return False

        # Map name include / exclude filter
        map_name = replay.map_name.lower()

        map_name_must_include = [i.strip().lower() for i in self.map_name_must_include.strip().split(",") if i.strip()]
        map_name_matches_include = False
        if map_name_must_include:
            for search_string in map_name_must_include:
                if search_string in map_name:
                    map_name_matches_include = True
            if not map_name_matches_include:
                return False

        map_name_must_exclude = [i.strip().lower() for i in self.map_name_must_exclude.strip().split(",") if i.strip()]
        map_name_matches_exclude = False
        if map_name_must_exclude:
            for search_string in map_name_must_exclude:
                if search_string in map_name:
                    map_name_matches_exclude = True
            if map_name_matches_exclude:
                return False
        return True
