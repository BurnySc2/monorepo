# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

from hypothesis import given, settings
from hypothesis import strategies as st

import python_examples.discrete_structures.primes


@given(n=st.integers(min_value=1, max_value=10**6))
def test_fuzz_is_prime(n):
    python_examples.discrete_structures.primes.is_prime(n=n)


@given(n=st.integers(min_value=1, max_value=10**6))
def test_fuzz_next_prime(n):
    python_examples.discrete_structures.primes.next_prime(n=n)


@given(n=st.integers(min_value=1, max_value=10**6), primes=st.none())
def test_fuzz_prime_factors(n, primes):
    python_examples.discrete_structures.primes.prime_factors(n=n, primes=primes)


@settings(max_examples=20, deadline=2_000)
@given(limit=st.integers(min_value=1, max_value=10**6))
def test_fuzz_sieve_of_eratosthenes(limit):
    python_examples.discrete_structures.primes.sieve_of_eratosthenes(limit=limit)
