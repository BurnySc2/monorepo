# https://projecteuler.net/problem=108
import math
import strformat

let LIMIT = 10^2

proc solve108(): int =
    # var n = 720720 # Best seem to be divisible by 40, or 720720
    # var n = 147026880
    var n = 1
    var bestSoFar: tuple[n, ways: int]
    while true:
        var factor = 2
        var ways = 0
        var lastFactorFound = -1
        while true:
            let denominatorY = n * factor
            let numeratorY = factor
            if denominatorY mod (numeratorY - 1) == 0:
                # If divisible, then X is (denominatorY / (numeratorY - 1))
                ways += 1
                lastFactorFound = factor
                let x = denominatorY div (numeratorY - 1)
                echo fmt"{n=}, {x=}, y={denominatorY}"
                if ways > 1000:
                    echo "Found solution:"
                    return n
                # Smaller denominator reached minimum
                if x == n - 1:
                    break
            factor += 1
            # If no factor has been found, cancel
            if lastFactorFound > 0 and factor > lastFactorFound * 2:
                echo fmt"{n}: {ways} ways (1)"
                if ways > bestSoFar.ways:
                    bestSoFar = (n, ways)
                    # Status report
                    # echo fmt"{n}: {ways} ways (1)"
                break
            if lastFactorFound == -1 and factor > n^2:
                echo fmt"{n}: {ways} ways (2)"
                break
        n += 1
        if n > LIMIT:
            echo fmt"Reached {LIMIT} and havent found an 'n'"
            break

when isMainModule:
    # TODO incomplete, takes forever
    # nim c -r -d:release p108.nim
    echo solve108()