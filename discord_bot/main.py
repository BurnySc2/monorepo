import asyncio
import os
from pathlib import Path
from typing import AsyncIterable

import hikari
from commands.public_remind import Remind
from hikari import Embed, GatewayGuild, GuildMessageCreateEvent
from loguru import logger

# Load key and start bot
DISCORDKEY_PATH = Path(__file__).parent / 'DISCORDKEY'
assert DISCORDKEY_PATH.is_file(), f"File '{DISCORDKEY_PATH}' not found"
with DISCORDKEY_PATH.open() as f:
    os.environ['DISCORDKEY'] = f.read()
bot = hikari.GatewayBot(token=os.getenv('DISCORDKEY'))  # type: ignore
PREFIX = '!'

# Start reminder plugin
my_reminder: Remind = Remind(bot)

# Load stage
assert os.getenv('STAGE', 'DEV') in {'DEV', 'PROD'}, os.getenv('STAGE', 'DEV')
STAGE = os.getenv('STAGE', 'DEV')

# Paths and folders of permanent data
DATA_FOLDER = Path(__file__).parent / 'data'
logger.add(DATA_FOLDER / 'bot.log')


async def reminder(event: GuildMessageCreateEvent, message: str):
    author = event.get_member()
    channel = event.get_channel()
    if not author or not channel:
        return
    response = await my_reminder.public_remind_in(event, message)
    if isinstance(response, Embed):
        sent_message = await channel.send(f'@{author.display_name}', embed=response)
    else:
        sent_message = await channel.send(f'@{author.display_name} {response}')
    # https://www.fileformat.info/info/unicode/char/274c/index.htm
    await sent_message.add_reaction('\u274C')


logger.add(DATA_FOLDER / 'bot.log')


async def remindat(event: GuildMessageCreateEvent, message: str):
    author = event.get_member()
    channel = event.get_channel()
    if not author or not channel:
        return
    response = await my_reminder.public_remind_at(event, message)
    if isinstance(response, Embed):
        sent_message = await channel.send(f'{author.mention}', embed=response)
    else:
        sent_message = await channel.send(f'{author.mention} {response}')
    # https://www.fileformat.info/info/unicode/char/274c/index.htm
    await sent_message.add_reaction('\u274C')


async def reminders(event: GuildMessageCreateEvent):
    author = event.get_member()
    channel = event.get_channel()
    if not author or not channel:
        return
    response = await my_reminder.public_list_reminders(event)
    if isinstance(response, Embed):
        message = await channel.send(f'{author.mention}', embed=response)
        # https://www.fileformat.info/info/unicode/char/274c/index.htm
        await message.add_reaction('\u274C')
    elif response:
        # No reminders
        await channel.send(f'{author.mention} {response}')


async def delreminder(event: GuildMessageCreateEvent, message: str):
    author = event.get_member()
    channel = event.get_channel()
    if not author or not channel:
        return
    response = await my_reminder.public_del_remind(event, message)
    if isinstance(response, Embed):
        sent_message = await channel.send(f'{author.mention}', embed=response)
        # https://www.fileformat.info/info/unicode/char/274c/index.htm
        await sent_message.add_reaction('\u274C')
    elif response:
        # Error message
        await channel.send(f'{author.mention} {response}')


async def loop_function():
    """ A function that is called every X seconds based on the asyncio.sleep(time) below. """
    while 1:
        await asyncio.sleep(1)
        await my_reminder.tick()


def is_command(cmd_name: str, content: str) -> bool:
    """Check if the message sent is a valid command."""
    return content == f'{PREFIX}{cmd_name}'


async def get_all_servers() -> AsyncIterable[GatewayGuild]:
    server: GatewayGuild
    all_connected_servers = bot.cache.get_available_guilds_view()
    for server in all_connected_servers.values():
        yield server

    # all_connected_servers = bot.cache.get_guilds_view()
    # for server in all_connected_servers.values():
    #     yield server

    # async for server in bot.rest.fetch_my_guilds():
    #     yield server


@bot.listen()
async def on_start(_event: hikari.StartedEvent) -> None:
    logger.info('Server started')
    await my_reminder.load_reminders()
    # Call another async function that runs forever
    asyncio.create_task(loop_function())
    async for server_name in get_all_servers():
        logger.info(f'Connected to server: {server_name}')


# pylint: disable=R0911
@bot.listen()
async def handle_reaction_add(event: hikari.GuildReactionAddEvent) -> None:
    if event.member.is_bot:
        return

    # Remove message if :x: was reacted to it
    if not event.is_for_emoji('\u274C'):
        return

    channel: hikari.PartialChannel = await bot.rest.fetch_channel(event.channel_id)
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
async def handle_new_message(event: hikari.GuildMessageCreateEvent) -> None:
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
        await handle_commands(command, message, event)


async def handle_commands(command: str, message: str, event: hikari.GuildMessageCreateEvent) -> None:
    if command == 'reminder':
        await reminder(event, message)
    if command == 'remindat':
        await remindat(event, message)
    if command == 'reminders':
        await reminders(event)
    if command == 'delreminder':
        await delreminder(event, message)

    if command == 'ping':
        guild = event.get_guild()
        if guild:
            b = await guild.fetch_emojis()
            animated = next(i for i in b if i.is_animated)
            await event.message.respond(f'Pong! {bot.heartbeat_latency * 1_000:.0f}ms {b[0]} {animated}')


if __name__ == '__main__':
    bot.run()
