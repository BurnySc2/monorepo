import random

import arrow
import hypothesis.strategies as st
import pytest
from hypothesis import example, given, settings

from commands._remind_parse import extract_groups, parse_time_shift
from commands.public_remind import Remind


def create_time_shift_string(_day, _hour, _minute, _second):
    days = ["d", "day", "days"]
    hours = ["h", "hour", "hours"]
    minutes = ["m", "min", "mins", "minute", "minutes"]
    seconds = ["s", "sec", "secs", "second", "seconds"]
    space = ["", " "]

    shift_list = []
    for time, time_strings in zip([_day, _hour, _minute, _second], [days, hours, minutes, seconds]):
        if time >= 0:
            # Random use of "6 days" or "6days"
            space_characer = random.choice(space)
            time_string = random.choice(time_strings)
            # pyrefly: ignore
            shift_list.append(f"{time}{space_characer}{time_string}")
            # Sometimes insert a space character after "6days"
            if random.choice(space):
                shift_list.append(" ")

    shift = "".join(shift_list)
    return shift.strip()


@settings(max_examples=100)
@example(_day=1_000_000, _hour=0, _minute=0, _second=0, _message="a")
@example(_day=0, _hour=1_000_000, _minute=0, _second=0, _message="a")
@example(_day=0, _hour=0, _minute=1_000_000, _second=0, _message="a")
@example(_day=0, _hour=0, _minute=0, _second=1_000_000, _message="a")
@given(
    # Day
    st.integers(min_value=0, max_value=1_000_000),
    # Hour
    st.integers(min_value=0, max_value=1_000_000),
    # Minute
    st.integers(min_value=0, max_value=1_000_000),
    # Second
    st.integers(min_value=0, max_value=1_000_000),
    # Message
    st.text(min_size=1),
)
@pytest.mark.asyncio
async def test_parsing_date_and_time_from_message_success(_day, _hour, _minute, _second, _message: str):
    # Dont care about empty strings, or just space or just new line characters
    if not _message.strip():
        return
    # Dont care about [0, 0, 0, 0]
    if not (_day or _hour or _minute or _second):
        return

    r = Remind(client=None)

    time_shift = create_time_shift_string(_day, _hour, _minute, _second)
    my_message = f"{time_shift} {_message}"
    result = await r._parse_time_shift_from_message(my_message)
    assert result is not None

    assert isinstance(result[0], arrow.Arrow)
    assert result[1] == _message.strip()


@settings(max_examples=100)
@example(_day=10_000_000, _hour=0, _minute=0, _second=0, _message="a")
@example(_day=0, _hour=10_000_000, _minute=0, _second=0, _message="a")
@example(_day=0, _hour=0, _minute=10_000_000, _second=0, _message="a")
@example(_day=0, _hour=0, _minute=0, _second=10_000_000, _message="a")
@given(
    # Day
    st.integers(min_value=0),
    # Hour
    st.integers(min_value=0),
    # Minute
    st.integers(min_value=0),
    # Second
    st.integers(min_value=0),
    # Message
    st.text(min_size=1),
)
@pytest.mark.asyncio
async def test_parsing_date_and_time_from_message_failure(_day, _hour, _minute, _second, _message):
    r = Remind(client=None)

    time_shift = create_time_shift_string(_day, _hour, _minute, _second)
    my_message = f"{time_shift} {_message}"

    result = await r._parse_time_shift_from_message(my_message)

    # Dont care about empty strings, or just space or just new line characters
    if not _message.strip():
        assert result is None
        return

    # Invalid day
    if not 0 <= _day <= 1_000_000:
        assert result is None
    # Invalid hour
    if not 0 <= _hour <= 1_000_000:
        assert result is None
    # Invalid minute
    if not 0 <= _minute <= 1_000_000:
        assert result is None
    # Invalid second
    if not 0 <= _second <= 1_000_000:
        assert result is None


def test_pure_parse_time_shift_success():
    now = arrow.get("2026-01-01T00:00:00+00:00")
    result = parse_time_shift("5d 3h 2m 1s hello world", now)
    assert result is not None
    future, text = result
    assert isinstance(future, arrow.Arrow)
    assert text == "hello world"
    assert future == now.shift(days=5, hours=3, minutes=2, seconds=1)


def test_pure_parse_time_shift_matches_wrapper():
    import asyncio

    now = arrow.utcnow()
    msg = "1d 1h hello"
    pure = parse_time_shift(msg, now)
    wrapped = asyncio.run(Remind(client=None)._parse_time_shift_from_message(msg))
    assert pure is not None
    assert wrapped is not None
    # Same reminder text; timestamps within a few seconds (now drift)
    assert pure[1] == wrapped[1]
    assert abs((pure[0] - wrapped[0]).total_seconds()) < 10


def test_pure_parse_time_shift_failure_cases():
    now = arrow.utcnow()
    assert parse_time_shift("", now) is None
    assert parse_time_shift("   ", now) is None
    assert parse_time_shift("hello without time", now) is None
    # Ridiculous values rejected
    assert parse_time_shift("10000000d hi", now) is None
    # Empty reminder text rejected
    assert parse_time_shift("5d ", now) is None


def test_extract_groups_time_shift():
    import re

    pattern = "(?:([0-9]+) ?(?:d|day|days))? ?((?:.|\n)+)"
    m = re.fullmatch(pattern, "5d hello")
    assert m is not None
    groups = extract_groups("5d hello", m)
    assert groups == ["5", "hello"]
