from __future__ import annotations

import asyncio
import re
import time

import arrow
from hikari import Embed, GatewayBot, GuildMessageCreateEvent, Message, NotFoundError, User
from loguru import logger

from cache import get_db
from prisma import models


MIN_SECONDS_ELAPSED_BEFORE_FETCH = 10 * 60 # 10 minutes

class Remind:
    REMINDER_ERROR_EMBED = Embed(
        title="Usage of reminder command",
        description="""
Example usage:
!reminder 5d 3h 2m 1s remind me of this
!reminder 1day 1hour 1min 1second remind me of this
!reminder 5days 3hours 2mins 420seconds remind me of this
        """,
    )

    def __init__(self, client: GatewayBot):
        super().__init__()
        self.client: GatewayBot = client
        self.next_reminder: models.Reminder | None = None
        # Limit of reminders per person
        self.reminder_limit = 20
        self.last_reminder_fetch: float = 0

    async def fetch_next_reminder(self) -> None:
        async with get_db() as db:
            next_reminder = await db.reminder.find_first(order=[{"reminder_utc": "asc"}])
            if next_reminder is not None:
                self.next_reminder = next_reminder

    async def tick(self):
        """Function gets called every second."""
        reminded: bool = True
        utc_now = arrow.utcnow().datetime

        # Fetch next reminder if none is loaded
        if self.next_reminder is None and MIN_SECONDS_ELAPSED_BEFORE_FETCH < time.time() - self.last_reminder_fetch:  # noqa: SIM300
            self.last_reminder_fetch = time.time()
            await self.fetch_next_reminder()

        while self.next_reminder is not None and reminded is True:
            reminded = False
            if self.next_reminder.reminder_utc < utc_now:
                # Run remind, remind user in discord
                reminded = True
                person: User = await self._get_user_by_id(self.next_reminder.user_id)
                logger.info(f"Attempting to remind {person.username} of: {self.next_reminder.message}")
                try:
                    # The original !reminder message may have been deleted
                    message: Message = await self._get_message_by_id(
                        self.next_reminder.channel_id,
                        self.next_reminder.message_id,
                    )
                    link: str = message.make_link(message.guild_id) + "\n"
                except NotFoundError:
                    link = ""
                await person.send(f"{link}You wanted to be reminded of: {self.next_reminder.message}")

                # Remove reminder from db
                async with get_db() as db:
                    await db.reminder.delete(where={"id": self.next_reminder.id})
                    self.next_reminder = None

                # Fetch next reminder
                await self.fetch_next_reminder()

    async def _get_user_by_id(self, user_id: int) -> User:
        return await self.client.rest.fetch_user(user_id)

    async def _get_message_by_id(self, channel_id: int, message_id: int) -> Message:
        return await self.client.rest.fetch_message(channel_id, message_id)

    async def _user_reached_max_reminder_threshold(self, user_id: int) -> bool:
        async with get_db() as db:
            count = await db.reminder.count(where={"user_id": user_id})
            return count >= self.reminder_limit

    async def _parse_date_and_time_from_message(self, message: str) -> tuple[arrow.Arrow, str] | None:
        time_now: arrow.Arrow = arrow.utcnow()

        # Old pattern which was working:
        date_pattern = r"(?:(?:(\d{4})-)?(\d{1,2})-(\d{1,2}))?"
        time_pattern = r"(?:(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?)?"
        text_pattern = "((?:.|\n)+)"
        space_pattern = " ?"
        regex_pattern = f"{date_pattern}{space_pattern}{time_pattern}{space_pattern} {text_pattern}"

        result = re.fullmatch(regex_pattern, message)

        # Pattern does not match
        if result is None:
            return None

        results = [(message[x[0] : x[1]] if x != (-1, -1) else "") for x in result.regs]
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
        hour, minute, second = (v.zfill(2) for v in [hour, minute, second])

        try:
            future_reminder_time = arrow.get(
                f"{str(year).zfill(2)}-{str(month).zfill(2)}-{str(day).zfill(2)} "
                f"{str(hour).zfill(2)}:{str(minute).zfill(2)}:{str(second).zfill(2)}",
                ["YYYY-MM-DD HH:mm:ss"],
            )
        except (ValueError, arrow.parser.ParserError):
            # Exception: ParserError not the right format
            return None
        return future_reminder_time, reminder_message.strip()

    async def _parse_time_shift_from_message(self, message: str) -> tuple[arrow.Arrow, str] | None:
        time_now: arrow.Arrow = arrow.utcnow()

        days_pattern = "(?:([0-9]+) ?(?:d|day|days))?"
        hours_pattern = "(?:([0-9]+) ?(?:h|hour|hours))?"
        minutes_pattern = "(?:([0-9]+) ?(?:m|min|mins|minute|minutes))?"
        seconds_pattern = "(?:([0-9]+) ?(?:s|sec|secs|second|seconds))?"
        text_pattern = "((?:.|\n)+)"
        space_pattern = " ?"
        regex_pattern = (
            f"{days_pattern}{space_pattern}{hours_pattern}{space_pattern}{minutes_pattern}{space_pattern}"
            f"{seconds_pattern} {text_pattern}"
        )

        result = re.fullmatch(regex_pattern, message)

        # Pattern does not match
        if result is None:
            return None

        results = [(message[x[0] : x[1]] if x != (-1, -1) else "") for x in result.regs]
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
        days_, hours_, minutes_, seconds_ = (v.zfill(1) for v in [day, hour, minute, second])
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
        """Reminds the user in a couple days, hours or minutes with a certain message."""
        threshold_reached: bool = await self._user_reached_max_reminder_threshold(event.author_id)
        if threshold_reached:
            return f"You have reached the limit of {self.reminder_limit} reminders."

        result = await self._parse_time_shift_from_message(reminder_message)
        if result is None:
            return self.REMINDER_ERROR_EMBED

        future_reminder_time, reminder_message = result

        channel = event.get_channel()
        guild = event.get_guild()
        if not channel or not guild:
            return
        async with get_db() as db:
            await db.reminder.create(
                data={
                    "reminder_utc": future_reminder_time.datetime,
                    "user_id": event.author_id,
                    "user_name": event.author.username,
                    "guild_id": guild.id,
                    "channel_id": channel.id,
                    "message": reminder_message,
                    "message_id": event.message_id,
                }
            )
        # New reminder might be newer than currently cached reminder
        await self.fetch_next_reminder()

        # Tell the user that the reminder was added successfully
        output_message: str = f"You will be reminded {future_reminder_time.humanize()} of: {reminder_message}"
        return output_message

    async def public_remind_at(
        self,
        _bot: GatewayBot,
        event: GuildMessageCreateEvent,
        reminder_message: str,
    ):
        """Add a reminder which reminds you at a certain time or date."""
        threshold_reached: bool = await self._user_reached_max_reminder_threshold(event.author_id)
        if threshold_reached:
            return f"You have reached the limit of {self.reminder_limit} reminders."

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
        error_embed: Embed = Embed(title="Usage of remindat command", description=error_description)

        result = await self._parse_date_and_time_from_message(reminder_message)
        if result is None:
            return error_embed
        future_reminder_time, reminder_message = result

        channel = event.get_channel()
        guild = event.get_guild()
        if not channel or not guild:
            return
        if time_now < future_reminder_time:
            async with get_db() as db:
                await db.reminder.create(
                    data={
                        "reminder_utc": future_reminder_time.datetime,
                        "user_id": event.author_id,
                        "user_name": event.author.username,
                        "guild_id": guild.id,
                        "channel_id": channel.id,
                        "message": reminder_message,
                        "message_id": event.message_id,
                    }
                )
            # New reminder might be newer than currently cached reminder
            await self.fetch_next_reminder()

            # Tell the user that the reminder was added successfully
            output_message: str = f"You will be reminded {future_reminder_time.humanize()} of: {reminder_message}"
            return output_message

        # TODO Fix embed for reminders in the past
        # Check if reminder is in the past, error invalid, reminder must be in the future
        return Embed(
            title="Usage of remindat command", description=f"Your reminder is in the past!\n{error_description}"
        )

    async def public_list_reminders(
        self,
        _bot: GatewayBot,
        event: GuildMessageCreateEvent,
        _message: str,
    ):
        """List all of the user's reminders"""
        # id, time formatted by iso standard format, in 5 minutes, text
        user_reminders: list[tuple[int, str, str, str]] = []

        # Sorted reminders by date and time ascending
        async with get_db() as db:
            user_reminders2 = await db.reminder.find_many(order=[{"reminder_utc": "asc"}])

        if len(user_reminders2) == 0:
            return "You don't have any reminders."

        reminder_id = 1
        while user_reminders2:
            r: models.Reminder = user_reminders2.pop(0)
            time: arrow.Arrow = arrow.get(r.reminder_utc)
            user_reminders.append((reminder_id, str(time), time.humanize(), r.message))
            reminder_id += 1

        reminders: list[str] = [
            f"{reminder_id}) {time} {humanize}: {message}" for reminder_id, time, humanize, message in user_reminders
        ]
        description: str = "\n".join(reminders)
        embed: Embed = Embed(title=f"{event.author.username}'s reminders", description=description)
        return embed

    async def public_del_remind(
        self,
        _bot: GatewayBot,
        event: GuildMessageCreateEvent,
        message: str,
    ):
        """Removes reminders from the user"""
        try:
            reminder_id_to_delete = int(message) - 1
        except ValueError:
            # Error: message is not valid
            # TODO Replace "!" with bot variable
            error_title = "Invalid usage of !delreminder"
            embed_description = "If you have 3 reminders, a valid command is is:\n!delreminder 2"
            embed = Embed(title=error_title, description=embed_description)
            return embed

        async with get_db() as db:
            user_reminders = await db.reminder.find_many(order=[{"reminder_utc": "asc"}])
            if 0 <= reminder_id_to_delete <= len(user_reminders) - 1:
                reminder_to_delete: models.Reminder = user_reminders[reminder_id_to_delete]
                # Find the reminder in the reminder list, then remove it
                logger.info(f"Trying to remove reminder {reminder_to_delete}")
                logger.info(f"Reminders available: {user_reminders}")
                await db.reminder.delete(where={"id": reminder_to_delete.id})

                # Say that the reminder was successfully removed?
                embed = Embed(
                    title=f"Removed {event.author.username}'s reminder", description=f"{reminder_to_delete.message}"
                )
                return embed

        # Invalid reminder id, too high number
        if len(user_reminders) == 0:
            return "Invalid reminder id, you have no reminders."
        if len(user_reminders) == 1:
            return "Invalid reminder id, you only have one reminders. Only '!delreminder 1' works for you."
        return (
            f"Invalid reminder id, you only have {len(user_reminders)} reminders. "
            f"Pick a number between 1 and {len(user_reminders)}."
        )


def main():
    message = "16:20 some message"
    message = "04-20 16:20 some message"
    # message = "01-01 00:00:00 0\n0"
    # message = "01-01 00:00:00 0"
    # message = "16:20"
    # message = ""
    r = Remind(None)
    result = asyncio.run(r._parse_date_and_time_from_message(message))
    print(result, bool(result[1]))
    assert result[1] == "some message"

    class CustomAuthor:
        def __init__(self, id_: int, name: str):
            self.id = id_
            self.name = name

    class CustomMessage:
        def __init__(self, content: str, author: CustomAuthor):
            self.content = content
            self.author = author

    author = CustomAuthor(420, "BuRny")

    my_message = "!remindat 5m text"
    a = arrow.get(
        "12:30",
        ["YYYY-MM-DD HH:mm:ss", "MM-DD HH:mm:ss", "MM-DD HH:mm", "YYYY-MM-DD", "MM-DD", "HH:mm:ss", "HH:mm"],
    )
    print(a)
    print(a.second)
    _message: CustomMessage = CustomMessage(my_message, author=author)
    _remind = Remind(client=None)
    # asyncio.run(remind.public_remind_at(message))


if __name__ == "__main__":
    main()
