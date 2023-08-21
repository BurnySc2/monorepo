import ../examples/math/is_prime
import unittest

static: assert 9 == 9, "Compile time assert"

suite "math test suite":
    assert not isPrime(1)
    assert isPrime(2)
    assert isPrime(3)
    assert not isPrime(4)
    assert isPrime(5)
    assert not isPrime(6)
    assert isPrime(7)
    assert not isPrime(8)
    assert isPrime(11)
