from typing import List


def sieve_of_eratosthenes(limit: int) -> List[int]:
    if limit < 2:
        return [False, False][:limit]
    sieve = [True for _ in range(0, limit)]
    sieve[:2] = [False, False]
    sieve[4::2] = [False] * len(sieve[4::2])

    value = 3
    primes = [2]
    while value < limit:
        if sieve[value]:
            primes.append(value)
            sieve[value ** 2 :: value] = [False] * len(sieve[value ** 2 :: value])
        value += 2
    return primes


class Solution:
    def countPrimes(self, n: int) -> int:
        if n <= 2:
            return 0
        return len(sieve_of_eratosthenes(n))
