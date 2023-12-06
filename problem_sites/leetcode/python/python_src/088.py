from typing import List


class Solution:
    def merge(self, nums1: List[int], m: int, nums2: List[int], n: int):
        """
        Do not return anything, modify nums1 in-place instead.
        """
        index1 = 0
        index2 = 0
        # Remove zeros from the end
        for i in range(len(nums1) - m):
            nums1.pop()
        while 1:
            if index1 >= len(nums1) or index2 >= len(nums2):
                break
            value1 = nums1[index1]
            value2 = nums2[index2]
            if value2 < value1:
                nums1.insert(index1, value2)
                index2 += 1
            else:
                index1 += 1
        # Append the rest from nums 2
        for i in range(index2, len(nums2)):
            nums1.append(nums2[i])
        return nums1


# fmt: off
test_cases = [
    [[1, 2, 3, 0, 0, 0], 3, [2, 5, 6], 3],
    [[1, 2, 5, 0, 0, 0], 3, [1, 2, 3], 3],
]
results = [
    [1, 2, 2, 3, 5, 6],
    [1, 1, 2, 2, 3, 5],
]
# fmt: on

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_result = app.merge(*test_case)
        assert (
            my_result == correct_result
        ), f"My result: {my_result}, correct result: {correct_result}\nTest Case: {test_case}"
