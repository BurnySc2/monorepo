# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

from hypothesis import given
from hypothesis import strategies as st

import python_examples.examples.other.regex_example


@given(n=st.integers(min_value=1, max_value=4000))
def test_fuzz_generate_roman_number(n):
    python_examples.examples.other.regex_example.generate_roman_number(n=n)


@given(roman_number=st.text())
def test_fuzz_regex_match_roman_number(roman_number):
    python_examples.examples.other.regex_example.regex_match_roman_number(roman_number=roman_number)
