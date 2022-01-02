# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

from typing import List

import deal
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from python_examples.examples.other.multiprocessing_example import cpu_bound_summing, do_math, do_math_async, find_sums


@deal.cases(do_math)
def test_do_math(case):
    _result = case()


@given(st.one_of(st.integers(), st.floats(min_value=-10**15, max_value=10**15)))
@pytest.mark.asyncio
async def test_do_math_async(number: float):
    result = await do_math_async(number)
    assert result == number + 3


@given(number=st.integers(min_value=0, max_value=10_000))
def test_fuzz_cpu_bound_summing(number):
    cpu_bound_summing(number=number)


@deal.cases(cpu_bound_summing)
def test_cpu_bound_summing(case):
    _result = case()


@settings(max_examples=10)
@given(numbers=st.lists(st.integers(min_value=0, max_value=1_000), min_size=1, max_size=100))
def test_find_sums(numbers: List[int]):
    _result = find_sums(numbers)