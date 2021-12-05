import hypothesis.strategies as st
import pytest
from hypothesis import given

from python_examples.main import do_math


@pytest.mark.asyncio
async def test_do_math():
    res = await do_math(7)
    assert res == 10


@pytest.mark.asyncio
@given(st.one_of(st.integers(), st.floats(allow_infinity=False, allow_nan=False)))
async def test_do_math_integers(value):
    assert 3 + value == await do_math(value)
