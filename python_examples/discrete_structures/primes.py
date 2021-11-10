import math
from collections import Counter
from typing import Counter as TypingCounter
from typing import List


def sieve_of_eratosthenes(limit: int) -> List[int]:
    if limit < 2:
        return []
    sieve = [True for _ in range(limit)]
    sieve[:2] = [False, False]
    sieve[4::2] = [False] * len(sieve[4::2])

    value = 3
    primes = [2]
    while value < limit:
        if sieve[value]:
            primes.append(value)
            sieve[value**2::value] = [False] * len(sieve[value**2::value])
        value += 2
    return primes


def prime_factors(n: int, primes: List[int] = None) -> Counter:
    if primes is None:
        primes = sieve_of_eratosthenes(int(n**0.5 + 1))
    i = 0
    factors: TypingCounter[int] = Counter()
    while n > 1 and i < len(primes):
        prime = primes[i]
        assert prime <= n
        while n % prime == 0:
            factors[prime] += 1
            n //= prime
        i += 1
    if n > 1:
        factors[n] += 1
    return factors


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    # For python 3.8: math.isqrt()
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True


def next_prime(n: int):
    if n < 2:
        return 2
    if n == 2:
        return 3
    n += 1 if n % 2 == 0 else 2
    while 1:
        if is_prime(n):
            return n
        n += 2


def test_prime_functions():
    for i in range(0, 100):
        sieve_of_eratosthenes(i)
    for i in sieve_of_eratosthenes(100):
        assert is_prime(i), (i, is_prime(i))

    not_primes = set(range(100)) - set(sieve_of_eratosthenes(100))
    for i in not_primes:
        assert not is_prime(i), (i, is_prime(i))

    prime_factors_dict = {
        0: Counter(),
        1: Counter(),
        2: Counter({2: 1}),
        3: Counter({3: 1}),
        4: Counter({2: 2}),
        5: Counter({5: 1}),
        6: Counter({
            2: 1,
            3: 1,
        }),
        7: Counter({7: 1}),
        8: Counter({2: 3}),
        9: Counter({3: 2}),
        10: Counter({
            2: 1,
            5: 1,
        }),
        11: Counter({11: 1}),
        12: Counter({
            2: 2,
            3: 1,
        }),
        13: Counter({13: 1}),
        14: Counter({
            2: 1,
            7: 1,
        }),
        15: Counter({
            3: 1,
            5: 1,
        }),
        16: Counter({2: 4}),
        17: Counter({17: 1}),
        18: Counter({
            3: 2,
            2: 1,
        }),
        19: Counter({19: 1}),
        20: Counter({
            2: 2,
            5: 1,
        }),
    }

    for i in range(100):
        # prime_factors(i)
        print(i, prime_factors(i))
        if i in prime_factors_dict:
            assert prime_factors(i) == prime_factors_dict[i]


if __name__ == '__main__':
    test_prime_functions()
