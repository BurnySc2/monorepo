import std/threadpool
import sequtils
import math

{.experimental: "parallel".}

proc cpuBoundSumming*(number: int): int =
    toSeq(1..number+1).sum

proc doMultiprocessing(amountProcesses: int): int =
    var myResults = newSeq[int](amountProcesses)
    parallel:
        for i in 0..myResults.high:
            myResults[i] = spawn(cpuBoundSumming((i + 1) * 1_000_000))
    myResults.sum

when isMainModule:
    # Use this when you dont care about the result
    # for i in 0..myResults.high:
    #     spawn(cpuBoundSumming((i + 1) * 1_000_000))
    # sync()

    echo doMultiprocessing(4)
