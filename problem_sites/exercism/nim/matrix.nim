# https://exercism.org/tracks/nim/exercises/matrix
import strutils, sugar

proc parseMatrix*(s: string): seq[seq[int]] =
    collect:
        for myRow in s.splitLines:
            collect:
                for value in myRow.splitWhitespace:
                    value.parseInt

proc row*(s: string, n: int): seq[int] =
    parseMatrix(s)[n-1]
    
proc column*(s: string, n: int): seq[int] =
    collect:
        for row in parseMatrix(s):
            for i, value in row:
                if i == n - 1:
                    value