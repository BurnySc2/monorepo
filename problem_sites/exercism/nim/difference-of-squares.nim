# https://exercism.org/tracks/nim/exercises/difference-of-squares
import math
import sequtils

proc squareOfSum*(n: int): int =
    toSeq(1..n).sum ^ 2

proc sumOfSquares*(n: int): int =
    for i in 1..n:
        result += i ^ 2

proc difference*(n: int): int =
    squareOfSum(n) - sumOfSquares(n)