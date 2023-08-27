# https://exercism.org/tracks/nim/exercises/isogram
import strutils

proc isIsogram*(s: string): bool =
    var found: set[char]
    for i in s.toLower:
        if i in [' ', '-']:
            continue
        if i in found:
            return false
        found.incl i
    true
