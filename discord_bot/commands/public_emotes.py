import re
from collections import Counter
from dataclasses import dataclass
from typing import Counter as CounterType
from typing import List, Optional, Union

from arrow import Arrow
from hikari import Embed, GatewayBot, GuildMessageCreateEvent, KnownCustomEmoji
from postgrest import APIResponse, AsyncSelectRequestBuilder  # pyre-ignore[0]
from simple_parsing import ArgumentParser

from db import DiscordMessage, supabase

# How many emojis to list when counting
TOP_EMOTE_LIMIT = 10


@dataclass
class CountEmotesParserOptions:
    # TODO: add user to check emotes from other users
    all: bool = False
    nostatic: bool = False
    noanimated: bool = False
    days: Optional[float] = None


public_count_emotes_parser = ArgumentParser()
public_count_emotes_parser.add_arguments(CountEmotesParserOptions, dest='params')


# pylint: disable=R0912
async def public_count_emotes(
    bot: GatewayBot,
    event: GuildMessageCreateEvent,
    message: str,
) -> Union[str, Embed]:
    unknown_args: List[str]
    try:
        parsed, unknown_args = public_count_emotes_parser.parse_known_args(args=message.split())
    except SystemExit:
        return 'Unable to parse input'
    if unknown_args:
        return f"Unknown params: {' '.join(unknown_args)}\n{public_count_emotes_parser.format_help()}"
    params: CountEmotesParserOptions = parsed.params

    query: AsyncSelectRequestBuilder = (
        supabase.table(DiscordMessage.table_name()).select(
            'what',
        )
        # Get messages written in that guild
        .eq(
            'guild_id',
            event.guild_id,
        )
        # Get messages with content similar to those of emojis
        .like(
            'what',
            '<%:%>',
        )
    )
    if not params.all:
        # Get messages by author_id
        query = query.eq(
            'author_id',
            event.author_id,
        )
    if params.days is not None:
        after: Arrow = Arrow.utcnow().shift(days=-params.days)
        query = query.gt('when', str(after))

    result_emotes: APIResponse = await query.execute()

    # What emotes to include in response
    if params.nostatic and params.noanimated:
        return '\'--nostatic\' and \'--noanimated\' does not work together'
    if params.noanimated:
        emote_pattern = r'<:([\d\w_]+):(\d+)>'
    elif params.nostatic:
        emote_pattern = r'<a:([\d\w_]+):(\d+)>'
    else:
        emote_pattern = r'<a?:([\d\w_]+):(\d+)>'

    emote_counter: CounterType[str] = Counter()
    for message_row in DiscordMessage.from_select(result_emotes):
        for match in re.finditer(emote_pattern, message_row.what):
            # Validate/load emoji from cache
            _emote_name, emote_snowflake = match.groups()
            find_emote: Optional[KnownCustomEmoji] = bot.cache.get_emoji(int(emote_snowflake))
            if find_emote is None:
                # Emote not found, must be from another server
                # Or false positive to regex match
                # emote_counter[emote_name] += 1
                pass
            elif find_emote.is_animated:
                # Emote can be rendered and is animated
                emote_counter[find_emote.mention] += 1
            elif find_emote.is_managed or find_emote.role_ids:
                # Requires subscriber status to display
                # emote_counter[emote_name] += 1
                pass
            else:
                # Emote can be rendered
                emote_counter[find_emote.mention] += 1

    emote_names_sorted_by_usage: List[str] = sorted(emote_counter, key=lambda i: emote_counter[i], reverse=True)
    emote_count: List[str] = [
        f'{emote_counter[name]} {name}' for index, name in enumerate(
            emote_names_sorted_by_usage,
            start=1,
        )
    ]
    emote_count = emote_count[:TOP_EMOTE_LIMIT]  # Only show top 10
    # TODO: Plot as chart, so that external emojis are included?
    description_text: str = f'Total emotes: {sum(emote_counter.values())}\n'
    description_text += '\n'.join(emote_count)
    title_name = 'Server' if params.all else f"{event.author.username}'s"
    embed = Embed(title=f'{title_name} top {TOP_EMOTE_LIMIT} used emotes', description=description_text)
    return embed
