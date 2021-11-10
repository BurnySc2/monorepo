import hypothesis.strategies as st
from hypothesis import given

from python_examples.examples.other.multiprocessing_example import cpu_bound_summing


@given(st.integers(min_value=0, max_value=10000))
def test_cpu_bound_summing(number):
    assert sum(i * i for i in range(number)) == cpu_bound_summing(number)
