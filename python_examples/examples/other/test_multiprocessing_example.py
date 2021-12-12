# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

from collections import ChainMap

import pytest
from hypothesis import given
from hypothesis import strategies as st

from python_examples.examples.other.multiprocessing_example import cpu_bound_summing, do_math, find_sums


@given(number=st.integers(min_value=0, max_value=1_000))
def test_fuzz_cpu_bound_summing(number):
    cpu_bound_summing(number=number)


@given(number=st.one_of(st.floats(), st.integers()))
@pytest.mark.asyncio
async def test_fuzz_do_math(number):
    await do_math(number=number)


@given(
    numbers=st.one_of(
        st.binary(),
        st.lists(st.integers(min_value=0, max_value=1_000)),
        st.sets(st.integers(min_value=0, max_value=1_000)),
        st.frozensets(st.integers(min_value=0, max_value=1_000)),
        st.dictionaries(
            keys=st.integers(min_value=0, max_value=1_000), values=st.integers(min_value=0, max_value=1_000)
        ),
        st.dictionaries(keys=st.integers(min_value=0, max_value=1_000),
                        values=st.none()).map(dict.keys),  # type: ignore
        st.dictionaries(
            keys=st.integers(min_value=0, max_value=1_000), values=st.integers(min_value=0, max_value=1_000)
        ).map(dict.values),  # type: ignore
        st.iterables(st.integers(min_value=0, max_value=1_000)),  # type: ignore
        st.dictionaries(
            keys=st.integers(min_value=0, max_value=1_000), values=st.integers(min_value=0, max_value=1_000)
        ).map(ChainMap),  # type: ignore
    )
)
def test_fuzz_find_sums(numbers):
    find_sums(numbers=numbers)
