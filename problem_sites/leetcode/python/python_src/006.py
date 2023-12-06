class Solution:
    def convert(self, s: str, numRows: int) -> str:
        rows = [[] for _ in range(numRows)]
        row_number = 0
        down = True
        for char in s:
            rows[row_number].append(char)
            if numRows > 1:
                if row_number == 0:
                    down = True
                elif row_number == numRows - 1:
                    down = False
                row_number += 1 if down else -1

        string_as_list = []
        for row in rows:
            string_as_list += row
        return "".join(string_as_list)


if __name__ == "__main__":
    # fmt: off
    test_cases = [
        ["PAYPALISHIRING", 3],
        ["PAYPALISHIRING", 4],
        ["AB", 1],
    ]
    results = [
        "PAHNAPLSIIGYIR",
        "PINALSIGYAHRPI",
        "AB"
    ]
    # fmt: on

    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_result = app.convert(*test_case)
        assert (
            my_result == correct_result
        ), f"My result: {my_result}, correct result: {correct_result}\nTest Case: {test_case}"
