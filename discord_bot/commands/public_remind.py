import asyncio
import json
import re
import sys
from heapq import heapify, heappop, heappush
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import arrow
from hikari import Embed, GatewayBot, GuildMessageCreateEvent, Message, NotFoundError, PartialChannel, User
from loguru import logger


class Reminder:

    def __init__(
        self,
        reminder_utc_timestamp: float = 0,
        user_id: int = 0,
        user_name: str = '',
        guild_id: int = 0,
        channel_id: int = 0,
        message: str = '',
        message_id: int = 0,
    ):
        self.reminder_utc_timestamp: float = reminder_utc_timestamp
        self.guild_id: int = guild_id
        self.channel_id: int = channel_id
        self.user_id: int = user_id
        self.user_name: str = user_name
        self.message: str = message
        self.message_id: int = message_id

    def __lt__(self, other: 'Reminder'):
        return self.reminder_utc_timestamp < other.reminder_utc_timestamp

    @staticmethod
    def from_dict(dictionary) -> 'Reminder':
        r: Reminder = Reminder()
        r.__dict__.update(dictionary)
        return r

    def to_dict(self) -> Dict[str, Union[float, str]]:
        return {
            'reminder_utc_timestamp': self.reminder_utc_timestamp,
            'guild_id': self.guild_id,
            'channel_id': self.channel_id,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'message': self.message,
            'message_id': self.message_id,
        }

    def __repr__(self) -> str:
        return f'Reminder({self.reminder_utc_timestamp} {self.guild_id} {self.channel_id} {self.user_id} {self.user_name} {self.message})'


class Remind:
    REMINDER_ERROR_EMBED = Embed(
        title='Usage of reminder command',
        description="""
Example usage:
!reminder 5d 3h 2m 1s remind me of this
!reminder 1day 1hour 1min 1second remind me of this
!reminder 5days 3hours 2mins 420seconds remind me of this
        """
    )

    def __init__(self, client: GatewayBot):
        super().__init__()
        self.client: GatewayBot = client
        self.reminders: List[Tuple[float, Reminder]] = []
        self.reminder_file_path: Path = Path(__file__).parent.parent / 'data' / 'reminders.json'
        # Limit of reminders per person
        self.reminder_limit = 10

    async def load_reminders(self):
        if self.reminder_file_path.is_file():
            with open(self.reminder_file_path) as f:
                reminders = json.load(f)
                # Append them in order in the minheap
                self.reminders = []
                for reminder in reminders:
                    r: Reminder = Reminder.from_dict(reminder)
                    heappush(self.reminders, (r.reminder_utc_timestamp, r))
        else:
            self.reminders = []
            await self.save_reminders()

    async def save_reminders(self):
        with open(self.reminder_file_path, 'w') as f:
            reminders_serialized = [reminder[1].to_dict() for reminder in self.reminders]
            json.dump(reminders_serialized, f, indent=2)

    async def tick(self):
        """ Function gets called every second. """
        need_to_save_reminders = False
        reminded: bool = True
        while self.reminders and reminded:
            reminded = False
            # First element, but is stored as tuple
            reminder: Reminder = self.reminders[0][1]
            reminder_time: arrow.Arrow = arrow.Arrow.utcfromtimestamp(reminder.reminder_utc_timestamp)
            time_now: arrow.Arrow = arrow.utcnow()
            if reminder_time < time_now:
                reminder = heappop(self.reminders)[1]
                need_to_save_reminders = True
                reminded = True
                person: User = await self._get_user_by_id(reminder.user_id)
                logger.info(f'Attempting to remind {person.username} of: {reminder.message}')
                try:
                    # The original !reminder message may have been deleted
                    message: Message = await self._get_message_by_id(reminder.channel_id, reminder.message_id)
                    link: str = message.make_link(message.guild_id) + '\n'
                except NotFoundError:
                    link = ''
                await person.send(f'{link}You wanted to be reminded of: {reminder.message}')

        # Save reminder to file because we did remind a person now
        if need_to_save_reminders:
            await self.save_reminders()

    async def _add_reminder(self, reminder: Reminder):
        heappush(self.reminders, (reminder.reminder_utc_timestamp, reminder))
        await self.save_reminders()

    async def _get_user_by_id(self, user_id: int) -> User:
        return await self.client.rest.fetch_user(user_id)

    async def _get_channel_by_id(self, channel_id: int) -> PartialChannel:
        return await self.client.rest.fetch_channel(channel_id)

    async def _get_message_by_id(self, channel_id: int, message_id: int) -> Message:
        return await self.client.rest.fetch_message(channel_id, message_id)

    async def _get_all_reminders_by_user_id(self, user_id: int) -> List[Reminder]:
        user_reminders: List[Reminder] = []
        reminders_copy = self.reminders.copy()
        while reminders_copy:
            r: Reminder = heappop(reminders_copy)[1]
            if user_id == r.user_id:
                user_reminders.append(r)
        return user_reminders

    async def _user_reached_max_reminder_threshold(self, user_id: int) -> bool:
        user_reminders = await self._get_all_reminders_by_user_id(user_id)
        return len(user_reminders) >= self.reminder_limit

    async def _parse_date_and_time_from_message(self, message: str) -> Optional[Tuple[arrow.Arrow, str]]:
        time_now: arrow.Arrow = arrow.utcnow()

        # Old pattern which was working:
        date_pattern = r'(?:(?:(\d{4})-)?(\d{1,2})-(\d{1,2}))?'
        time_pattern = r'(?:(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?)?'
        text_pattern = '((?:.|\n)+)'
        space_pattern = ' ?'
        regex_pattern = f'{date_pattern}{space_pattern}{time_pattern}{space_pattern} {text_pattern}'

        result = re.fullmatch(regex_pattern, message)

        # Pattern does not match
        if result is None:
            return None

        results = [(message[x[0]:x[1]] if x != (-1, -1) else '') for x in result.regs]
        _ = results.pop(0)
        year, month, day, hour, minute, second, reminder_message = results

        # Message is empty or just a new line character
        if not reminder_message.strip():
            return None

        # Could not retrieve a combination of month+day or hour+minute from the message
        if not all([month, day]) and not all([hour, minute]):
            return None

        # Set year to current year if it was not set in the message string
        year = year if year else str(time_now.year)
        # Set current month and day if the input was only HH:mm:ss
        month = month if month else str(time_now.month)
        day = day if day else str(time_now.day)

        # Fill empty strings with 1 zero
        hour, minute, second = [v.zfill(2) for v in [hour, minute, second]]

        try:
            future_reminder_time = arrow.get(
                f'{str(year).zfill(2)}-{str(month).zfill(2)}-{str(day).zfill(2)} {str(hour).zfill(2)}:{str(minute).zfill(2)}:{str(second).zfill(2)}',
                ['YYYY-MM-DD HH:mm:ss'],
            )
        except (ValueError, arrow.parser.ParserError):
            # Exception: ParserError not the right format
            return None
        return future_reminder_time, reminder_message.strip()

    # pylint: disable=R0914
    async def _parse_time_shift_from_message(self, message: str) -> Optional[Tuple[arrow.Arrow, str]]:
        time_now: arrow.Arrow = arrow.utcnow()

        days_pattern = '(?:([0-9]+) ?(?:d|day|days))?'
        hours_pattern = '(?:([0-9]+) ?(?:h|hour|hours))?'
        minutes_pattern = '(?:([0-9]+) ?(?:m|min|mins|minute|minutes))?'
        seconds_pattern = '(?:([0-9]+) ?(?:s|sec|secs|second|seconds))?'
        text_pattern = '((?:.|\n)+)'
        space_pattern = ' ?'
        regex_pattern = f'{days_pattern}{space_pattern}{hours_pattern}{space_pattern}{minutes_pattern}{space_pattern}{seconds_pattern} {text_pattern}'

        result = re.fullmatch(regex_pattern, message)

        # Pattern does not match
        if result is None:
            return None

        results = [(message[x[0]:x[1]] if x != (-1, -1) else '') for x in result.regs]
        _ = results.pop(0)
        day, hour, minute, second, reminder_message = results

        # Message is empty or just a new line character
        if not reminder_message.strip():
            return None

        # At least one value must be given
        valid_usage: bool = bool((day or hour or minute or second) and reminder_message)
        if not valid_usage:
            return None

        # Fill empty strings with 1 zero
        days_, hours_, minutes_, seconds_ = [v.zfill(1) for v in [day, hour, minute, second]]
        # Convert strings to int
        days, hours, minutes, seconds = map(int, [days_, hours_, minutes_, seconds_])

        # Do not do ridiculous reminders
        if any(time > 1_000_000 for time in [days, hours, minutes, seconds]):
            return None

        try:
            future_reminder_time = time_now.shift(days=days, hours=hours, minutes=minutes, seconds=seconds)
        # Days > 3_000_000 => error
        except OverflowError:
            return None
        return future_reminder_time, reminder_message.strip()

    async def public_remind_in(
        self,
        _bot: GatewayBot,
        event: GuildMessageCreateEvent,
        reminder_message: str,
    ):
        """ Reminds the user in a couple days, hours or minutes with a certain message. """
        threshold_reached: bool = await self._user_reached_max_reminder_threshold(event.author_id)
        if threshold_reached:
            user_reminders = await self._get_all_reminders_by_user_id(event.author_id)
            return f'You already have {len(user_reminders)} / {self.reminder_limit} reminders, which is higher than the limit.'

        result = await self._parse_time_shift_from_message(reminder_message)
        if result is None:
            return self.REMINDER_ERROR_EMBED

        future_reminder_time, reminder_message = result

        channel = event.get_channel()
        guild = event.get_guild()
        if not channel or not guild:
            return
        reminder: Reminder = Reminder(
            reminder_utc_timestamp=future_reminder_time.timestamp(),
            user_id=event.author_id,
            user_name=event.author.username,
            guild_id=guild.id,
            channel_id=channel.id,
            message=reminder_message,
            message_id=event.message_id,
        )
        await self._add_reminder(reminder)
        # Tell the user that the reminder was added successfully
        output_message: str = f'You will be reminded {future_reminder_time.humanize()} of: {reminder_message}'
        return output_message

    async def public_remind_at(
        self,
        _bot: GatewayBot,
        event: GuildMessageCreateEvent,
        reminder_message: str,
    ):
        """ Add a reminder which reminds you at a certain time or date. """
        threshold_reached: bool = await self._user_reached_max_reminder_threshold(event.author_id)
        if threshold_reached:
            user_reminders = await self._get_all_reminders_by_user_id(event.author_id)
            return f'You already have {len(user_reminders)} / {self.reminder_limit} reminders, which is higher than the limit.'

        time_now: arrow.Arrow = arrow.utcnow()

        error_description = """
Example usage:
!remindat 2021-04-20 04:20:00 remind me of this
!remindat 2021-04-20 04:20 remind me of this
!remindat 04-20 04:20:00 remind me of this
!remindat 04-20 04:20 remind me of this
!remindat 2021-04-20 remind me of this
!remindat 04-20 remind me of this
!remindat 04:20:00 remind me of this
!remindat 04:20 remind me of this
        """
        error_embed: Embed = Embed(title='Usage of remindat command', description=error_description)

        result = await self._parse_date_and_time_from_message(reminder_message)
        if result is None:
            return error_embed
        future_reminder_time, reminder_message = result

        channel = event.get_channel()
        guild = event.get_guild()
        if not channel or not guild:
            return
        if time_now < future_reminder_time:
            reminder: Reminder = Reminder(
                reminder_utc_timestamp=future_reminder_time.timestamp(),
                user_id=event.author_id,
                user_name=event.author.username,
                guild_id=guild.id,
                channel_id=channel.id,
                message=reminder_message,
                message_id=event.message_id,
            )
            await self._add_reminder(reminder)
            # Tell the user that the reminder was added successfully
            output_message: str = f'You will be reminded {future_reminder_time.humanize()} of: {reminder.message}'
            return output_message

        # TODO Fix embed for reminders in the past
        # Check if reminder is in the past, error invalid, reminder must be in the future
        return Embed(
            title='Usage of remindat command', description=f'Your reminder is in the past!\n{error_description}'
        )

    async def public_list_reminders(
        self,
        _bot: GatewayBot,
        event: GuildMessageCreateEvent,
        _message: str,
    ):
        """ List all of the user's reminders """
        # id, time formatted by iso standard format, in 5 minutes, text
        user_reminders: List[Tuple[int, str, str, str]] = []

        # Sorted reminders by date and time ascending
        user_reminders2: List[Reminder] = await self._get_all_reminders_by_user_id(event.author_id)
        reminder_id = 1
        while user_reminders2:
            r: Reminder = user_reminders2.pop(0)
            time: arrow.Arrow = arrow.Arrow.utcfromtimestamp(r.reminder_utc_timestamp)
            user_reminders.append((reminder_id, str(time), time.humanize(), r.message))
            reminder_id += 1

        if not user_reminders:
            return "You don't have any reminders."

        reminders: List[str] = [
            f'{reminder_id}) {time} {humanize}: {message}' for reminder_id, time, humanize, message in user_reminders
        ]
        description: str = '\n'.join(reminders)
        embed: Embed = Embed(title=f"{event.author.username}'s reminders", description=description)
        return embed

    async def public_del_remind(
        self,
        _bot: GatewayBot,
        event: GuildMessageCreateEvent,
        message: str,
    ):
        """ Removes reminders from the user """
        try:
            reminder_id_to_delete = int(message) - 1
        except ValueError:
            # Error: message is not valid
            # TODO Replace "!" with bot variable
            error_title = 'Invalid usage of !delreminder'
            embed_description = 'If you have 3 reminders, a valid command is is:\n!delreminder 2'
            embed = Embed(title=error_title, description=embed_description)
            return embed

        user_reminders = await self._get_all_reminders_by_user_id(event.author_id)
        if 0 <= reminder_id_to_delete <= len(user_reminders) - 1:
            reminder_to_delete: Reminder = user_reminders[reminder_id_to_delete]
            # Find the reminder in the reminder list, then remove it
            logger.info(f'Trying to remove reminder {reminder_to_delete}')
            logger.info(f'Reminders available: {self.reminders}')
            self.reminders.remove((reminder_to_delete.reminder_utc_timestamp, reminder_to_delete))
            heapify(self.reminders)
            await self.save_reminders()
            # Say that the reminder was successfully removed?
            embed = Embed(
                title=f"Removed {event.author.username}'s reminder", description=f'{reminder_to_delete.message}'
            )
            return embed

        # Invalid reminder id, too high number
        if len(user_reminders) == 0:
            return 'Invalid reminder id, you have no reminders.'
        if len(user_reminders) == 1:
            return "Invalid reminder id, you only have one reminders. Only '!delreminder 1' works for you."
        return f'Invalid reminder id, you only have {len(user_reminders)} reminders. Pick a number between 1 and {len(user_reminders)}.'


def main():
    message = '16:20 some message'
    message = '04-20 16:20 some message'
    # message = "01-01 00:00:00 0\n0"
    # message = "01-01 00:00:00 0"
    # message = "16:20"
    # message = ""
    r = Remind(None)
    # pylint: disable=W0212
    result = asyncio.run(r._parse_date_and_time_from_message(message))
    print(result, bool(result[1]))
    assert result[1] == 'some message'
    sys.exit()

    class CustomAuthor:

        def __init__(self, id_: int, name: str):
            self.id = id_
            self.name = name

    class CustomMessage:

        def __init__(self, content: str, author: CustomAuthor):
            self.content = content
            self.author = author

    author = CustomAuthor(420, 'BuRny')

    my_message = '!remindat 5m text'
    a = arrow.get(
        '12:30',
        ['YYYY-MM-DD HH:mm:ss', 'MM-DD HH:mm:ss', 'MM-DD HH:mm', 'YYYY-MM-DD', 'MM-DD', 'HH:mm:ss', 'HH:mm'],
    )
    print(a)
    print(a.second)
    _message: CustomMessage = CustomMessage(my_message, author=author)
    _remind = Remind(client=None)
    # asyncio.run(remind.public_remind_at(message))


if __name__ == '__main__':
    main()
