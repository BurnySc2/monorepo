# https://exercism.org/tracks/nim/exercises/two-fer
from std/strformat import fmt

proc twoFer*(name = ""): string =
    result = "One for you, one for me."
    if name != "":
        result = fmt"One for {name}, one for me."
