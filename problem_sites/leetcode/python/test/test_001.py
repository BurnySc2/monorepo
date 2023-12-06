from python_src.p001_two_sum import Solution


def test_001():
    assert Solution().twoSum([2, 7, 11, 15], 9) == [0, 1]


def test_002(benchmark):
    benchmark(Solution().twoSum, [2, 7, 11, 15], 9)
