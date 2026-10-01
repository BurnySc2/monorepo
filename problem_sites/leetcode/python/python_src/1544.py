class Solution:
    def makeGood(self, s: str) -> str:
        i = 0
        string = list(s)
        while i < len(string) - 1:
            a = string[i]
            b = string[i + 1]
            if a.lower() == b.lower() and a != b:
                string.pop(i)
                string.pop(i)
                i = 0
            else:
                i += 1
        return "".join(string)


if __name__ == "__main__":
    # fmt: off
    test_cases = [
        "leEeetcode",
        "abBAcC",
    ]
    results = [
        "leetcode",
        "",
    ]
    # fmt: on

    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_result = app.makeGood(test_case)
        assert (
            my_result == correct_result
        ), f"My result: {my_result}, correct result: {correct_result}\nTest Case: {test_case}"
