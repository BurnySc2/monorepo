# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

from hypothesis import given
from hypothesis import strategies as st

import python_examples.discrete_structures.combination


@given(my_list=st.lists(st.builds(object)), n=st.integers())
def test_fuzz_combination_generator(my_list, n):
    python_examples.discrete_structures.combination.combination_generator(my_list=my_list, n=n)


@given(iterable=st.lists(st.builds(object)), replacement=st.integers())
def test_fuzz_combinations_with_replacement_generator(iterable, replacement):
    python_examples.discrete_structures.combination.combinations_with_replacement_generator(
        iterable=iterable, replacement=replacement
    )


@given(repeat=st.integers())
def test_fuzz_product_generator(repeat):
    python_examples.discrete_structures.combination.product_generator(repeat=repeat)
