# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

from hypothesis import given, settings
from hypothesis import strategies as st

import python_examples.examples.other.roman_numbers


@settings(deadline=1000)
@given(n=st.integers(min_value=1, max_value=4000))
def test_fuzz_generate_roman_number(n):
    python_examples.examples.other.roman_numbers.generate_roman_number(n=n)
