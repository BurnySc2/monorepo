from dataclasses import dataclass

# https://discordpy.readthedocs.io/en/latest/api.html
from typing import List, Optional

import aiohttp
from hikari.guilds import Member

# http://zetcode.com/python/prettytable/
from prettytable import PrettyTable  # pip install PTable


@dataclass()
class Sc2LadderResult:
    realm: int
    # One of US, EU, KR
    region: str
    # One of Master GrandMaster etc
    rank: str
    username: str
    # Battle tag with #number
    bnet_id: str
    # One of Zerg Terran Protoss Random
    race: str
    mmr: int
    wins: int
    losses: int
    # Clantag or None if not given
    clan: Optional[str]
    profile_id: int
    alias: Optional[str]

    @property
    def short_race(self) -> str:
        return self.race[0]

    @property
    def short_league(self):
        league_dict = {
            'grandmaster': 'GM',
            'master': 'M',
            'diamond': 'D',
            'platinum': 'P',
            'gold': 'G',
            'silver': 'S',
            'bronze': 'B',
        }
        return league_dict[self.rank.lower()]

    def format_result(self) -> List[str]:
        return [
            f'{self.region} {self.short_race} {self.short_league}',
            f'{self.mmr}',
            f'{self.wins}-{self.losses}',
            f'{self.username[:18]}',
            f"{self.alias[:18] if self.alias else ''}",
        ]


async def public_mmr(_author: Member, query_name: str):
    """The public command '!mmr name', will look up an account name, clan name or stream name and list several results as a markdown table using PrettyTable
    Usage:
    !mmr twitch.tv/rotterdam08
    !mmr rotterdam
    !mmr [zelos]"""
    # Correct usage
    assert query_name
    async with aiohttp.ClientSession() as session:
        # It might fit 15 results in discord
        url = f'https://www.sc2ladder.com/api/player?query={query_name}&results=15'
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
            fields = ['S-R-L', 'MMR', 'W/L', 'Username', 'Alias']
            pretty_table = PrettyTable(field_names=fields)
            pretty_table.border = False
            for api_result in results:
                result_object = Sc2LadderResult(**api_result)
                formated_result = result_object.format_result()
                pretty_table.add_row(formated_result)
            query_link = f'<https://www.sc2ladder.com/search?query={query_name}>'
            return f'{query_link}\n```md\n{len(results)} results for {query_name}:\n{pretty_table}```'
