# https://www.codewars.com/kata/514b92a657cdc65150000006/train/nim
import sugar, math
proc solution*(n: int): int =
    let numbers = collect:
        for i in 1..<n:
            if i mod 3 == 0 or i mod 5 == 0: i
    numbers.sum