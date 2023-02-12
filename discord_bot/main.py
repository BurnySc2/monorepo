import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator, Awaitable, Callable, Set, Union

import hikari.errors
import httpx
import postgrest
from hikari import (
    Embed,
    GatewayBot,
    GatewayGuild,
    GuildMessageCreateEvent,
    GuildReactionAddEvent,
    GuildTextChannel,
    Intents,
    Message,
    OwnGuild,
    PartialChannel,
    StartedEvent,
)
from hikari.channels import ChannelType
from loguru import logger
from postgrest import APIResponse

from commands.public_emotes import public_count_emotes
from commands.public_mmr import public_mmr
from commands.public_remind import Remind
from commands.public_twss import public_twss
from db import DiscordMessage, DiscordQuotes, supabase

# Load key from env or from file
token = os.getenv('DISCORDKEY')
if token is None:
    DISCORDKEY_PATH = Path(__file__).parent / 'DISCORDKEY'
    assert DISCORDKEY_PATH.is_file(
    ), f"File '{DISCORDKEY_PATH}' not found, you can get it from https://discord.com/developers/applications/<bot_id>/bot"
    with DISCORDKEY_PATH.open() as f:
        token = f.read().strip()
bot = GatewayBot(token=token, intents=Intents.ALL)  # type: ignore
del token

PREFIX = '!'

# Start reminder plugin
my_reminder: Remind = Remind(bot)

# Load stage via env variable
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
    # Call the given function with the bot, event and message
    response: Union[Embed, str] = await function_to_call(bot, event, message)
    if isinstance(response, Embed):
        sent_message = await channel.send(f'{event.author.mention}', embed=response)
    else:
        # Error message or raw string response
        sent_message = await channel.send(f'{event.author.mention} {response}')
    if add_remove_emoji:
        # https://www.fileformat.info/info/unicode/char/274c/index.htm
        await sent_message.add_reaction('\u274C')


async def loop_function() -> None:
    """ A function that is called every X seconds based on the asyncio.sleep(time) below. """
    while 1:
        await asyncio.sleep(1)
        await my_reminder.tick()


async def get_text_channels_of_server(server: OwnGuild) -> AsyncGenerator[GuildTextChannel, None]:
    assert isinstance(server, OwnGuild), type(server)
    for channel in await bot.rest.fetch_guild_channels(server):  # type: ignore
        if channel.type not in {ChannelType.GUILD_TEXT}:
            continue
        assert isinstance(channel, GuildTextChannel), type(channel)
        yield channel


async def add_message_to_db(server_id: int, channel_id: int, message: Message) -> None:
    """Insert message into database. Ignore if it's a duplicate"""
    try:
        await (
            supabase.table(DiscordMessage.table_name()).insert(
                {
                    'message_id': message.id,
                    'guild_id': server_id,
                    'channel_id': channel_id,
                    'author_id': message.author.id,
                    'who': str(message.author),
                    'when': str(message.created_at),
                    'what': message.content,
                }
            ).execute()
        )
    except postgrest.exceptions.APIError:
        logger.error(f"Mesage already exists or could not insert message: {message.id}")


async def insert_messages_of_channel_to_db(server: OwnGuild, channel: GuildTextChannel) -> None:
    # Check if bot has access to channel
    if channel.last_message_id is None:
        return
    try:
        _temp_message = await channel.fetch_message(channel.last_message_id)
    except hikari.errors.ForbiddenError:
        logger.error(f"No access to channel '{channel}' in server '{server}'")
        return
    except hikari.errors.NotFoundError:
        logger.error(f"Last message in channel '{channel}' in server '{server}' could not be fetched")
        return

    all_message_ids_response: APIResponse = await supabase.table(DiscordMessage.table_name()).select('message_id').eq(
        "channel_id",
        channel.id,
    ).execute()
    message_ids_already_exist_in_db: Set[int] = {row['message_id'] for row in all_message_ids_response.data}

    messages_inserted_count = 0
    async for message in channel.fetch_history():
        # Don't process duplicates
        if message.id in message_ids_already_exist_in_db:
            continue
        # Ignore bot and webhook messages
        if message.author.is_bot:
            continue
        # TODO Use bulk insert via List[dict] once API allows it
        # logger.info(f"Inserting message from {message.created_at}")
        await add_message_to_db(server.id, channel.id, message)
        messages_inserted_count += 1
    if messages_inserted_count > 0:
        logger.info(f"Inserted {messages_inserted_count} messages of channel '{channel}' in server '{server}'")


async def get_all_servers() -> AsyncGenerator[GatewayGuild, None]:
    try:
        _check_if_supabase_is_up: APIResponse = await supabase.table(DiscordMessage.table_name()).select(
            'message_id',
        ).limit(1).execute()
    except httpx.ConnectError as e:
        logger.trace(f'Error trying to access supabase: {e}')
        return

    server: OwnGuild
    async for server in bot.rest.fetch_my_guilds():
        yield server
        if STAGE == 'PROD':
            # Add all messages to DB
            async for channel in get_text_channels_of_server(server):
                # Create a coroutine that works in background to add messages of specific server and channel to database
                asyncio.create_task(insert_messages_of_channel_to_db(server, channel))


@bot.listen()
async def on_start(_event: StartedEvent) -> None:
    logger.info('Bot started')
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

    channel: PartialChannel = await bot.rest.fetch_channel(event.channel_id)
    # Use channel 'bot_tests' only for development
    if STAGE == 'DEV' and channel.name != 'bot_tests':
        return
    if STAGE == 'PROD' and channel.name == 'bot_tests':
        return

    message: Message = await bot.rest.fetch_message(event.channel_id, event.message_id)
    if not message:
        return

    # Message is by bot
    # Message has mention
    # Mention is same user who reacted
    # Remove message if :x: was reacted to it
    if message.author.is_bot and f'<@{event.user_id}>' not in message.content and event.is_for_emoji('\u274C'):
        await message.delete()
        return

    # If "twss" reacted and reaction count >=3: add quote to db
    allowed_emoji_names = {"twss"}
    target_emoji_count = 4
    if not message.author.is_bot and event.emoji_name in allowed_emoji_names:
        for reaction in message.reactions:
            if reaction.emoji.name in allowed_emoji_names and reaction.count >= target_emoji_count:
                try:
                    # Add quote to db
                    await (
                        supabase.table(DiscordQuotes.table_name()).insert(
                            {
                                'message_id': message.id,
                                'guild_id': event.guild_id,
                                'channel_id': event.channel_id,
                                'author_id': message.author.id,
                                'who': str(message.author),
                                'when': str(message.created_at),
                                'what': message.content,
                                'emoji_name': reaction.emoji.name,
                            }
                        ).execute()
                    )
                    logger.info(f"Added quote: {message.content}")
                    # TODO Write message to channel that a quote has been added and how many there are now in total
                except postgrest.exceptions.APIError as e:
                    if e.message != f'duplicate key value violates unique constraint "{DiscordQuotes.table_name()}_pkey"':
                        raise
                    logger.error(f"Quote already exists: {message.id}")
                return
        return


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

    # On new message, add message to DB
    await add_message_to_db(event.guild_id, event.channel_id, event.message)

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
        'twss': public_twss,
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
        if not guild:
            return
        b = await guild.fetch_emojis()

        animated = next(i for i in b if i.is_animated)
        await event.message.respond(f'Pong! {bot.heartbeat_latency * 1_000:.0f}ms {b[0]} {animated}')


if __name__ == '__main__':
    bot.run()
