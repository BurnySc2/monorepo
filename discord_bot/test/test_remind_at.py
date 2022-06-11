import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import asyncio

import arrow
import hypothesis.strategies as st
import pytest
from commands.public_remind import Remind
from hypothesis import example, given, settings


def create_date_time_string(_year: int, _month: int, _day: int, _hour: int, _minute: int, _second: int) -> str:
    # Mark _year=0 as year not being used
    if _year:
        date = f'{str(_year).zfill(4)}-{str(_month).zfill(2)}-{str(_day).zfill(2)}'
    else:
        date = f'2000-{str(_month).zfill(2)}-{str(_day).zfill(2)}'

    # Mark _second=0 as second not being used
    if _second:
        time = f'{str(_hour).zfill(2)}:{str(_minute).zfill(2)}:{str(_second).zfill(2)}'
    else:
        time = f'{str(_hour).zfill(2)}:{str(_minute).zfill(2)}'

    # Convert input time to date_time combination
    date_time = ''
    if date:
        if time:
            date_time = f'{date} {time}'
        else:
            date_time = f'{date}'
    elif time:
        date_time = f'{time}'

    return date_time


@pytest.mark.asyncio
@settings(max_examples=100)
@given(
    # Year
    st.integers(min_value=0, max_value=9999),
    # Month
    st.integers(min_value=1, max_value=12),
    # Day
    st.integers(min_value=1, max_value=28),
    # Hour
    st.integers(min_value=0, max_value=23),
    # Minute
    st.integers(min_value=0, max_value=59),
    # Second
    st.integers(min_value=0, max_value=59),
    # Message
    st.text(min_size=1),
)
async def test_parsing_date_and_time_from_message_success(_year, _month, _day, _hour, _minute, _second, _message):
    # Dont care about empty strings, or just space or just new line characters
    if not _message.strip():
        return
    r = Remind(client=None)

    date_time = create_date_time_string(_year, _month, _day, _hour, _minute, _second)
    my_message = f'{date_time} {_message}'
    # pylint: disable=W0212
    result = await r._parse_date_and_time_from_message(my_message)

    assert isinstance(result[0], arrow.Arrow)
    assert result[1] == _message.strip()


# pylint: disable=R0912
@settings(max_examples=1000)
@given(
    # Year
    st.integers(),
    # Month
    st.integers(min_value=-10, max_value=15),
    # Day
    st.integers(min_value=-10, max_value=50),
    # Hour
    st.integers(min_value=-10, max_value=50),
    # Minute
    st.integers(min_value=-10, max_value=100),
    # Second
    st.integers(min_value=-10, max_value=100),
    # Message
    st.text(min_size=1),
)
@example(2021, 4, 20, 4, 20, 00, 'remind me of this')
def test_parsing_date_and_time_from_message_failure(_year, _month, _day, _hour, _minute, _second, _message):
    if not _message.strip():
        return
    r = Remind(client=None)

    date_time = create_date_time_string(_year, _month, _day, _hour, _minute, _second)
    my_message = f'{date_time} {_message}'

    # Invalid date time combination, e.g. 30th of february
    try:
        _arrow_time = arrow.get(date_time)
    except (ValueError, arrow.parser.ParserError):
        return
    date: str
    time: str
    date, time = date_time.split(' ')

    if date.count('-') == 2:
        arrow.get(date, 'YYYY-MM-DD')
    if date.count('-') == 1:
        arrow.get(date, 'MM-DD')
    if time.count(':') == 2:
        arrow.get(time, 'HH:mm:ss')
    if time.count(':') == 1:
        arrow.get(time, 'HH:mm')

    # pylint: disable=W0212
    result = asyncio.run(r._parse_date_and_time_from_message(my_message))

    if not date_time:
        assert result is None

    # Invalid year
    if not 0 <= _year < 10_000:
        assert result is None
    # Invalid month
    if not 0 < _month <= 12:
        assert result is None
    # Invalid day
    if not 0 < _day <= 31:
        assert result is None

    # Invalid hour
    if not 0 <= _hour < 24:
        assert result is None
    # Invalid minute
    if not 0 <= _minute < 60:
        assert result is None
    # Invalid second
    if not 0 <= _second < 60:
        assert result is None
    """
    TODO Write tests for all examples
    !remindat 2021-04-20 04:20:00 remind me of this
    !remindat 2021-04-20 04:20 remind me of this
    !remindat 04-20 04:20:00 remind me of this
    !remindat 04-20 04:20 remind me of this
    !remindat 2021-04-20 remind me of this
    !remindat 04-20 remind me of this
    !remindat 04:20:00 remind me of this
    !remindat 04:20 remind me of this
    """
