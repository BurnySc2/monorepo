# https://exercism.org/tracks/nim/exercises/largest-series-product
from sequtils import foldl
from sugar import collect
from strutils import allCharsInSet

proc largestProduct*(s: string, span: int): int =
    if s.len < span or s == "" or span <= 0 or not s.allCharsInSet({'0'..'9'}):
        raise new ValueError
    for i, _ in s[0..<(s.len + 1 - span)]:
        # Collect a sequence of 'span' characters in a row
        let mySeq = collect(newSeq):
            for i in s[i..(i + span - 1)]:
                # Convert and return the integer value
                i.ord - '0'.ord
        # Calculate result
        let product = mySeq.foldl(a * b, 1)
        # Store largest result
        result = result.max(product)