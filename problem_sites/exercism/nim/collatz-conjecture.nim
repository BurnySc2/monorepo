# https://exercism.org/tracks/nim/exercises/collatz-conjecture
import math

proc steps*(n: int): int =
    if n <= 0:
        raise new ValueError
    var value = n
    while value > 1:
        result.inc
        let (newValue, remainder) = value.divmod 2
        if remainder == 1:
            value = 3 * value + 1
            continue
        value = newValue
