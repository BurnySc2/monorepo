from python_src.p004 import Solution


def test_004_01():
    assert Solution().findMedianSortedArrays([1, 3], [2]) == 2.0
    assert Solution().findMedianSortedArrays([1, 2], [3, 4]) == 2.5


def test_004_02(benchmark):
    benchmark(Solution().findMedianSortedArrays, [1, 3], [2])


def test_004_03(benchmark):
    benchmark(Solution().findMedianSortedArrays, [1, 2], [3, 4])
