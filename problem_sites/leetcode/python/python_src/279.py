class Solution:
    def __init__(self):
        self.memory = {1: 1}
        self.max_memory = 1
        self.squares = [1, 4]
        self.squares_set = {1, 4}

    def add_squares(self, limit: int):
        while self.squares[-1] < limit:
            new = 2 * self.squares[-1] + 2 - self.squares[-2]
            self.squares.append(new)
            self.squares_set.add(new)

    def add_memory(self, n: int):
        if n in self.memory:
            return
        for i in range(self.max_memory + 1, n + 1):
            if i in self.squares_set:
                self.memory[i] = 1
            else:
                new_memory = min(self.memory[i - square] + 1 for square in self.squares if i > square)
                self.memory[i] = new_memory
        self.max_memory = n

    def numSquares(self, n: int) -> float:
        if n in self.memory:
            return self.memory[n]

        if n > self.squares[-1]:
            self.add_squares(n)

        self.add_memory(n)

        return self.memory[n]


if __name__ == "__main__":
    # fmt: off
    test_cases = [
        12,
        13,
        113,
        7168,
    ]
    results = [
        3,
        2,
        2,
        4,
    ]
    # fmt: on

    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        test_case_copy = test_case.copy() if hasattr(test_case, "copy") else test_case
        my_result = app.numSquares(test_case)
        assert (
            my_result == correct_result
        ), f"My result: {my_result}, correct result: {correct_result}\nTest Case: {test_case_copy}"
