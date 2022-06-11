import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import random

import arrow
import hypothesis.strategies as st
import pytest
from commands.public_remind import Remind
from hypothesis import example, given, settings


def create_time_shift_string(_day, _hour, _minute, _second):
    days = 'd day days'.split(' ')
    hours = 'h hour hours'.split(' ')
    minutes = 'm min mins minute minutes'.split(' ')
    seconds = 's sec secs second seconds'.split(' ')
    space = ['', ' ']

    shift_list = []
    for time, time_strings in zip([_day, _hour, _minute, _second], [days, hours, minutes, seconds]):
        if time >= 0:
            # Random use of "6 days" or "6days"
            space_characer = random.choice(space)
            time_string = random.choice(time_strings)
            shift_list.append(f'{time}{space_characer}{time_string}')
            # Sometimes insert a space character after "6days"
            if random.choice(space):
                shift_list.append(' ')

    shift = ''.join(shift_list)
    return shift.strip()


@pytest.mark.asyncio
@settings(max_examples=100)
@example(_day=1_000_000, _hour=0, _minute=0, _second=0, _message='a')
@example(_day=0, _hour=1_000_000, _minute=0, _second=0, _message='a')
@example(_day=0, _hour=0, _minute=1_000_000, _second=0, _message='a')
@example(_day=0, _hour=0, _minute=0, _second=1_000_000, _message='a')
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
async def test_parsing_date_and_time_from_message_success(_day, _hour, _minute, _second, _message):
    # Dont care about empty strings, or just space or just new line characters
    if not _message.strip():
        return
    # Dont care about [0, 0, 0, 0]
    if not (_day or _hour or _minute or _second):
        return

    r = Remind(client=None)

    time_shift = create_time_shift_string(_day, _hour, _minute, _second)
    my_message = f'{time_shift} {_message}'
    # pylint: disable=W0212
    result = await r._parse_time_shift_from_message(my_message)

    assert isinstance(result[0], arrow.Arrow)
    assert result[1] == _message.strip()


@pytest.mark.asyncio
@settings(max_examples=100)
@example(_day=10_000_000, _hour=0, _minute=0, _second=0, _message='a')
@example(_day=0, _hour=10_000_000, _minute=0, _second=0, _message='a')
@example(_day=0, _hour=0, _minute=10_000_000, _second=0, _message='a')
@example(_day=0, _hour=0, _minute=0, _second=10_000_000, _message='a')
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
async def test_parsing_date_and_time_from_message_failure(_day, _hour, _minute, _second, _message):
    r = Remind(client=None)

    time_shift = create_time_shift_string(_day, _hour, _minute, _second)
    my_message = f'{time_shift} {_message}'

    # pylint: disable=W0212
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
