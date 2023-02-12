from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import aiohttp
from hikari import GatewayBot, GuildMessageCreateEvent

# http://zetcode.com/python/prettytable/
from prettytable import PrettyTable  # pip install PTable

MESSAGE_CHARACTER_LIMIT = 2_000
TABLE_ROW_LIMIT = 20


@dataclass()
class Sc2LadderResult:
    realm: int
    # One of US, EU, KR
    region: str
    # One of Master GrandMaster etc
    # rank: str
    username: str
    # Battle tag with #number
    bnet_id: str
    # One of Zerg Terran Protoss Random
    race: str
    # Last or current season mmr
    mmr: str
    # Current season games played
    games_played: int
    # Clantag or None if not given
    clan_tag: Optional[str]

    @staticmethod
    def from_api_result(data: dict) -> Sc2LadderResult:

        members = data['members']
        character = members['character']
        previous_stats = data['previousStats']
        current_stats = data['currentStats']
        clan = members.get('clan')
        race = 'Random'
        if 'protossGamesPlayed' in members:
            race = 'Protoss'
        if 'terranGamesPlayed' in members:
            race = 'Terran'
        if 'zergGamesPlayed' in members:
            race = 'Zerg'
        mmr = '-'
        if previous_stats['rating']:
            mmr = str(previous_stats['rating'])
        if current_stats['rating']:
            mmr = str(current_stats['rating'])
        games_played = 0
        if current_stats['gamesPlayed']:
            games_played = current_stats['gamesPlayed']
        clan_tag = clan['tag'] if clan else None
        bnet_id = character['name']
        return Sc2LadderResult(
            realm=character['realm'],
            region=character['region'],
            bnet_id=bnet_id,
            race=race,
            mmr=mmr,
            games_played=games_played,
            clan_tag=clan_tag,
            username=bnet_id.split('#')[0],
        )

    @property
    def short_race(self) -> str:
        return self.race[0]

    @property
    def clan_tag_string(self) -> str:
        if self.clan_tag:
            return f'[{self.clan_tag}] '
        return ''

    def format_result(self) -> List[str]:
        return [
            f'{self.region} {self.short_race}',
            f'{self.mmr}',
            f'{self.games_played}',
            f'{self.clan_tag_string}{self.username[:18]}',
        ]


async def public_mmr(
    _bot: GatewayBot,
    _event: GuildMessageCreateEvent,
    query_name: str,
) -> str:
    """The public command '!mmr name', will look up an account name, clan name or stream name and list several results as a markdown table using PrettyTable
    Usage:
    !mmr burny"""
    # Correct usage
    assert query_name
    async with aiohttp.ClientSession() as session:
        # It might fit 15 results in discord
        url = f'https://www.nephest.com/sc2/api/characters?name={query_name}'
        async with session.get(url) as response:
            if response.status != 200:
                return f'Error: Status code `{response.status}` for query `{query_name}`'
            try:
                results = await response.json()
            except aiohttp.ContentTypeError:
                # Error with aiohttp with decoding
                return f'Error while trying to decode JSON with input: `{query_name}`'

            if not results:
                # No player found
                return f'No player found with name `{query_name}`'
            # Server, Race, League, MMR, Win/Loss, Name, Last Played, Last Streamed
            fields = ['S-R', 'MMR', 'Games', 'Name']
            parsed_results: List[Sc2LadderResult] = []
            for api_result in results:
                result_object: Sc2LadderResult = Sc2LadderResult.from_api_result(api_result)
                parsed_results.append(result_object)
            parsed_results.sort(key=lambda result: result.mmr, reverse=True)

            pretty_table = PrettyTable(field_names=fields)
            pretty_table.border = False
            for count, parsed_result in enumerate(parsed_results):
                copy: PrettyTable = pretty_table.copy()
                copy.add_row(parsed_result.format_result())
                # If message limit reached, stop adding results
                if len(str(copy)) > MESSAGE_CHARACTER_LIMIT - 100:
                    break
                # If table row limit is reached, stop adding results
                if count >= TABLE_ROW_LIMIT:
                    break
                pretty_table.add_row(parsed_result.format_result())

            query_link = f'<https://www.nephest.com/sc2/?type=search&name={query_name}#search>'
            return f'{query_link}\n```md\n{len(results)} results for {query_name}:\n{pretty_table}```'
