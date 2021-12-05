# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

from hypothesis import given
from hypothesis import strategies as st

import python_examples.discrete_structures.product


@given(repeat=st.integers())
def test_fuzz_product_generator(repeat):
    python_examples.discrete_structures.product.product_generator(repeat=repeat)
