"""Pure reminder message parsers with no hikari/DB imports.

This module contains the pure (synchronous, side-effect free) parsing logic
for :class:`commands.public_remind.Remind`.
It is intentionally free of ``hikari`` and database imports so it can be
unit-tested deterministically by injecting ``now``.
"""

from __future__ import annotations

import re

import arrow


def extract_groups(message: str, match: re.Match[str]) -> list[str]:
    """Extract captured groups from a regex match as strings.

    Non-participating optional groups are returned as ``""``, matching ``result.regs`` slicing semantics.

    :param message: Matched input string.
    :param match: Successful :func:`re.fullmatch` result.
    :return: List of group strings excluding the full match (group 0).
    """
    groups: list[str] = []
    for span in match.regs[1:]:
        if span == (-1, -1):
            groups.append("")
        else:
            groups.append(message[span[0] : span[1]])
    return groups


def parse_date_and_time(message: str, now: arrow.Arrow) -> tuple[arrow.Arrow, str] | None:
    """Parse absolute date/time reminder strings (pure).

    Supported forms (all followed by a reminder text)::

        YYYY-MM-DD HH:mm:ss text
        YYYY-MM-DD HH:mm text
        MM-DD HH:mm:ss text
        MM-DD HH:mm text
        YYYY-MM-DD text
        MM-DD text
        HH:mm:ss text
        HH:mm text

    :param message: Raw user message without the command prefix.
    :param now: Reference time (normally ``arrow.utcnow()``) used to fill
        in missing year/month/day components.
    :return: ``(future_time, reminder_text)`` or ``None`` if unparseable.
    """
    date_pattern = r"(?:(?:(\d{4})-)?(\d{1,2})-(\d{1,2}))?"
    time_pattern = r"(?:(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?)?"
    text_pattern = "((?:.|\n)+)"
    space_pattern = " ?"
    regex_pattern = f"{date_pattern}{space_pattern}{time_pattern}{space_pattern} {text_pattern}"

    result = re.fullmatch(regex_pattern, message)

    # Pattern does not match
    if result is None:
        return None

    year, month, day, hour, minute, second, reminder_message = extract_groups(message, result)

    # Message is empty or just a new line character
    if not reminder_message.strip():
        return None

    # Could not retrieve a combination of month+day or hour+minute from the message
    if not all([month, day]) and not all([hour, minute]):
        return None

    # Set year to current year if it was not set in the message string
    year = year if year else str(now.year)
    # Set current month and day if the input was only HH:mm:ss
    month = month if month else str(now.month)
    day = day if day else str(now.day)

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


def parse_time_shift(message: str, now: arrow.Arrow) -> tuple[arrow.Arrow, str] | None:
    """Parse relative time-shift reminder strings (pure).

    Example: ``5d 3h 2m 1s remind me of this``.

    :param message: Raw user message without the command prefix.
    :param now: Reference time (normally ``arrow.utcnow()``) to shift from.
    :return: ``(future_time, reminder_text)`` or ``None`` if unparseable
        or if any component exceeds 1_000_000.
    """
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

    day, hour, minute, second, reminder_message = extract_groups(message, result)

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
        future_reminder_time = now.shift(days=days, hours=hours, minutes=minutes, seconds=seconds)
    # Days > 3_000_000 => error
    except OverflowError:
        return None
    return future_reminder_time, reminder_message.strip()
