from typing import List


class Solution:
    def is_valid_square(self, board: List[List[str]], rows: List[int], columns: List[int]) -> bool:
        seen = set()
        for row in board[rows[0] : rows[1]]:
            for value in row[columns[0] : columns[1]]:
                if value == ".":
                    continue
                if value in seen:
                    return False
                seen.add(value)
        return True

    def is_valid_row(self, board: List[List[str]], row_number: int):
        seen = set()
        for row in board[row_number]:
            for value in row:
                if value == ".":
                    continue
                if value in seen:
                    return False
                seen.add(value)
        return True

    def is_valid_col(self, board: List[List[str]], col_number: int):
        seen = set()
        for row_number in range(9):
            value = board[row_number][col_number]
            if value == ".":
                continue
            if value in seen:
                return False
            seen.add(value)
        return True

    def isValidSudoku(self, board: List[List[str]]) -> bool:
        return (
            all(self.is_valid_square(board, [y, y + 3], [x, x + 3]) for y in range(0, 9, 3) for x in range(0, 9, 3))
            and all(self.is_valid_row(board, y) for y in range(0, 9))
            and all(self.is_valid_col(board, x) for x in range(0, 9))
        )


# fmt: off
test_cases = [
    [
        ["5", "3", ".", ".", "7", ".", ".", ".", "."],
        ["6", ".", ".", "1", "9", "5", ".", ".", "."],
        [".", "9", "8", ".", ".", ".", ".", "6", "."],
        ["8", ".", ".", ".", "6", ".", ".", ".", "3"],
        ["4", ".", ".", "8", ".", "3", ".", ".", "1"],
        ["7", ".", ".", ".", "2", ".", ".", ".", "6"],
        [".", "6", ".", ".", ".", ".", "2", "8", "."],
        [".", ".", ".", "4", "1", "9", ".", ".", "5"],
        [".", ".", ".", ".", "8", ".", ".", "7", "9"],
    ],
    [
        ["8", "3", ".", ".", "7", ".", ".", ".", "."],
        ["6", ".", ".", "1", "9", "5", ".", ".", "."],
        [".", "9", "8", ".", ".", ".", ".", "6", "."],
        ["8", ".", ".", ".", "6", ".", ".", ".", "3"],
        ["4", ".", ".", "8", ".", "3", ".", ".", "1"],
        ["7", ".", ".", ".", "2", ".", ".", ".", "6"],
        [".", "6", ".", ".", ".", ".", "2", "8", "."],
        [".", ".", ".", "4", "1", "9", ".", ".", "5"],
        [".", ".", ".", ".", "8", ".", ".", "7", "9"],
    ],
    [
        [".", ".", "4", ".", ".", ".", "6", "3", "."],
        [".", ".", ".", ".", ".", ".", ".", ".", "."],
        ["5", ".", ".", ".", ".", ".", ".", "9", "."],
        [".", ".", ".", "5", "6", ".", ".", ".", "."],
        ["4", ".", "3", ".", ".", ".", ".", ".", "1"],
        [".", ".", ".", "7", ".", ".", ".", ".", "."],
        [".", ".", ".", "5", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", ".", "."],
    ],
]
results = [True, False, False]
# fmt: on

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_result = app.isValidSudoku(test_case)
        assert (
            my_result == correct_result
        ), f"My result: {my_result}, correct result: {correct_result}\nTest Case: {test_case}"
