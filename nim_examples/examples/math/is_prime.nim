import math

proc isPrime*(n: Positive): bool =
    if n == 2:
        return true
    if n < 2 or n mod 2 == 0:
        return false
    var i = 3
    while i ^ 2 <= n:
        if n mod i == 0:
            return false
        i.inc(2)
    true
when isMainModule:
    assert not isPrime(1)
    assert isPrime(2)
    assert isPrime(3)
    assert not isPrime(4)
    assert isPrime(5)
    assert not isPrime(6)
    assert isPrime(7)
    assert not isPrime(8)
    assert isPrime(11)
