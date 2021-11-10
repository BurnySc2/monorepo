import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from python_examples.discrete_structures.permutation import _test_permutations


def test_permutations():
    _test_permutations(8)
