# https://exercism.org/tracks/nim/exercises/anagram
import tables, strutils

proc detectAnagrams*(word: string, candidates: openArray[string]): seq[string] =
    let target = toCountTable(word.toLower)
    for candidate in candidates:
        let myWord = toCountTable(candidate.toLower)
        if myWord == target and candidate.toLower != word.toLower:
            result.add(candidate)