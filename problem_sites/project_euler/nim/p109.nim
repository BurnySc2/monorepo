# https://projecteuler.net/problem=109
import tables
import strformat

proc solve109(): int =
    var availableMoves: OrderedTable[string, int]
    for factor, name in ["S", "D", "T"]:
        for number in 1..20:
            availableMoves[fmt"{name}{number}"] = (factor + 1) * number 
    availableMoves[fmt"SB"] = 25 # Single bullseye
    availableMoves[fmt"DB"] = 50 # Double bullseye

    var finishingMoves: Table[string, int]
    for number in 1..20:
        finishingMoves[fmt"D{number}"] = 2 * number 
    finishingMoves[fmt"DB"] = 50

    var moves: Table[string, int]
    for move1, score in finishingMoves:
        moves[move1] = score 

    for move1, score1 in availableMoves:
        for move2, score2 in finishingMoves:
            moves[fmt"{move1} {move2}"] = score1 + score2 

    for move1, score1 in availableMoves:
        for move2, score2 in availableMoves:
            for move3, score3 in finishingMoves:
                moves[fmt"{move1} {move2} {move3}"] = score1 + score2 + score3
            # However, the combination S1 T1 D1 is considered the same as T1 S1 D1.
            if move1 == move2:
                break

    for move, score in moves:
        if score < 100:
            result += 1

echo solve109()
