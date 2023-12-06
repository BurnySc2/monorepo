# https://exercism.org/tracks/nim/exercises/pangram
from strutils import toLower

proc isPangram*(s: string): bool =
    let allLetters = {'a'..'z'}
    var letters: set[char]
    for i in s.toLower():
        letters.incl(i)
        if letters >= allLetters:
            return true
