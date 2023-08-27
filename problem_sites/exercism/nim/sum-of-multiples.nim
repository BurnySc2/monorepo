# https://exercism.org/tracks/nim/exercises/sum-of-multiples
import sugar, sequtils, math

proc sum*(limit: int, factors: openArray[int]): int =
    var numbers = collect:
        for factor in factors:
            for i in 1..limit:
                let value = factor * i
                if value >= limit:
                    break
                value
    numbers.deduplicate.sum