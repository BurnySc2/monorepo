# 202
# https://leetcode.com/problems/happy-number/
# nim js -d:release -o:p202_happy_number.js p202_happy_number.nim
# nim js -d:danger -o:p202_happy_number.js p202_happy_number.nim
import math

# Didnt work, i suspect js large numbers problems
proc isHappy(n: var int): bool {.exportc.} =
    var seen = @[n]
    while true:
        var new_n, remainder: int
        while n > 0:
            # (n, remainder) = divmod(n, 10)
            remainder = n mod 10
            n = n div 10
            new_n += remainder ^ 2
        n = new_n
        if n == 1:
            return true 
        if n in seen:
            return false
        seen.add(n) 
