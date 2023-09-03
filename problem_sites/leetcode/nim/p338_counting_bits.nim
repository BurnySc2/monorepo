# 338. Counting Bits
# https://leetcode.com/problems/counting-bits/
# nim js -d:release -o:p338_counting_bits.js p338_counting_bits.nim
# nim js -d:danger -o:p338_counting_bits.js p338_counting_bits.nim
import math
import sugar

proc countBits(n: int): seq[int] {.exportc.} =
    let LIMIT = 10^5
    var last_exponent = 0
    let exponents = collect:
        for i in 1..20:
            if 2^i <= LIMIT:
                2^i
    for i in 0..n:
        if i in exponents:
            # Case 2, 4, 8, 16, ...
            last_exponent = i
            result.add(1)
        elif last_exponent == 0:
            # Case 0 and 1
            result.add(i)
        else:
            result.add(1 + result[i - last_exponent])
