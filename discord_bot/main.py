import asyncio
import os
from pathlib import Path
from typing import AsyncIterable, Awaitable, Callable, Set, Union

from hikari import (
    Embed,
    GatewayBot,
    GatewayGuild,
    GuildMessageCreateEvent,
    GuildReactionAddEvent,
    GuildTextChannel,
    PartialChannel,
    StartedEvent,
)
from loguru import logger

from discord_bot.commands.public_emotes import public_count_emotes
from discord_bot.commands.public_mmr import public_mmr
from discord_bot.commands.public_remind import Remind
from discord_bot.db import flatten_result, supabase

# Load key from env or from file
token = os.getenv('DISCORDKEY')
if token is None:
    DISCORDKEY_PATH = Path(__file__).parent / 'DISCORDKEY'
    assert DISCORDKEY_PATH.is_file(
    ), f"File '{DISCORDKEY_PATH}' not found, you can get it from https://discord.com/developers/applications/<bot_id>/bot"
    with DISCORDKEY_PATH.open() as f:
        token = f.read().strip()
bot = GatewayBot(token=token)  # type: ignore
del token

PREFIX = '!'

# Start reminder plugin
my_reminder: Remind = Remind(bot)

# Load stage
assert os.getenv('STAGE', 'DEV') in {'DEV', 'PROD'}, os.getenv('STAGE', 'DEV')
STAGE = os.getenv('STAGE', 'DEV')

# Paths and folders of permanent data
DATA_FOLDER = Path(__file__).parent / 'data'
logger.add(DATA_FOLDER / 'bot.log')


async def generic_command_caller(
    event: GuildMessageCreateEvent,
    function_to_call: Callable[[GatewayBot, GuildMessageCreateEvent, str], Awaitable[Union[Embed, str]]],
    message: str,
    add_remove_emoji: bool = False,
) -> None:
    """
    @param event
    @param function_to_call: A function to be called with the given message, expects function to return an Embed or string
    @param message: Parsed messaged by the user, without the command
    @param add_remove_emoji: If true, bot will react to its own message with a 'X' emoji
    so that the mentioned user can remove the bot message at will.
    """
    channel = event.get_channel()
    if not channel:
        return
    # Call the given function with the event and message
    response: Union[Embed, str] = await function_to_call(bot, event, message)
    if isinstance(response, Embed):
        sent_message = await channel.send(f'{event.author.mention}', embed=response)
    else:
        # Error message
        sent_message = await channel.send(f'{event.author.mention} {response}')
    if add_remove_emoji:
        # https://www.fileformat.info/info/unicode/char/274c/index.htm
        await sent_message.add_reaction('\u274C')


async def loop_function() -> None:
    """ A function that is called every X seconds based on the asyncio.sleep(time) below. """
    while 1:
        await asyncio.sleep(1)
        await my_reminder.tick()


async def get_all_servers() -> AsyncIterable[GatewayGuild]:
    all_connected_servers = bot.cache.get_available_guilds_view()
    server: GatewayGuild

    added_messages = await supabase.table('discord_messages').select('message_id').execute()
    message_ids_already_exist: Set[int] = set(flatten_result(added_messages, 'message_id'))

    for server in all_connected_servers.values():
        yield server
        # Add all messages from channel "chat" to DB
        if server.id == 384968030423351298:
            for channel in server.get_channels().values():
                if channel.name == 'chat' and isinstance(channel, GuildTextChannel):
                    async for message in channel.fetch_history():
                        if message.id in message_ids_already_exist:
                            continue
                        # TODO Use bulk insert via List[dict]
                        await (
                            supabase.table('discord_messages').insert(
                                {
                                    'message_id': message.id,
                                    'guild_id': server.id,
                                    'channel_id': channel.id,
                                    'author_id': message.author.id,
                                    'who': str(message.author),
                                    'when': str(message.created_at),
                                    'what': message.content,
                                }
                            ).execute()
                        )

    # all_connected_servers = bot.cache.get_guilds_view()
    # for server in all_connected_servers.values():
    #     yield server

    # async for server in bot.rest.fetch_my_guilds():
    #     yield server


@bot.listen()
async def on_start(_event: StartedEvent) -> None:
    logger.info('Server started')
    await my_reminder.load_reminders()
    # Call another async function that runs forever
    asyncio.create_task(loop_function())
    async for server_name in get_all_servers():
        logger.info(f'Connected to server: {server_name}')


# pylint: disable=R0911
@bot.listen()
async def handle_reaction_add(event: GuildReactionAddEvent) -> None:
    if event.member.is_bot:
        return

    # Remove message if :x: was reacted to it
    if not event.is_for_emoji('\u274C'):
        return

    channel: PartialChannel = await bot.rest.fetch_channel(event.channel_id)
    # Use channel 'bot_tests' only for development
    if STAGE == 'DEV' and channel.name != 'bot_tests':
        return
    if STAGE == 'PROD' and channel.name == 'bot_tests':
        return

    message = await bot.rest.fetch_message(event.channel_id, event.message_id)
    if not message:
        return
    # Message is not by this bot
    if not message.author.is_bot:
        return
    # Reaction is not by one of the mentioned users
    if not message.content or f'<@{event.user_id}>' not in message.content:
        return
    await message.delete()


@bot.listen()
async def handle_new_message(event: GuildMessageCreateEvent) -> None:
    """Listen for messages being created."""
    channel = event.get_channel()
    if not channel:
        return
    # Use channel 'bot_tests' only for development
    if STAGE == 'DEV' and channel.name != 'bot_tests':
        return
    if STAGE == 'PROD' and channel.name == 'bot_tests':
        return

    # Do not react if messages sent by webhook or bot, or message is empty
    if not event.is_human or not event.content:
        return

    # TODO On new message, add to DB

    # guild = event.get_guild()
    # member = event.get_member()
    #
    # # a = guild.get_emojis()
    # b = await guild.fetch_emojis()
    # animated = next(i for i in b if i.is_animated)

    if event.content.startswith(PREFIX):
        command, *message_list = event.content.split()
        command = command[len(PREFIX):]
        message = ' '.join(message_list)
        await handle_commands(event, command, message)


async def handle_commands(event: GuildMessageCreateEvent, command: str, message: str) -> None:
    function_mapping = {
        'reminder': my_reminder.public_remind_in,
        'remindat': my_reminder.public_remind_at,
        'reminders': my_reminder.public_list_reminders,
        'delreminder': my_reminder.public_del_remind,
        'mmr': public_mmr,
        'emotes': public_count_emotes,
    }
    if command in function_mapping:
        function = function_mapping[command]
        await generic_command_caller(
            event,
            function,
            message,
            add_remove_emoji=True,
        )

    if command == 'ping':
        guild = event.get_guild()
        if guild:
            b = await guild.fetch_emojis()

            animated = next(i for i in b if i.is_animated)
            await event.message.respond(f'Pong! {bot.heartbeat_latency * 1_000:.0f}ms {b[0]} {animated}')


if __name__ == '__main__':
    bot.run()
