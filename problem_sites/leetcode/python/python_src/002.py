from typing import List


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def addTwoNumbers(self, l1: ListNode, l2: ListNode) -> ListNode:
        first_number = None
        second_number = None
        while l1:
            if first_number is None:
                first_number = l1.val
            else:
                first_number *= 10 + l1.val
            l1 = l1.next
        return first_number + second_number


# fmt: off
# test_cases = [5]
# results = [[[1], [1, 1], [1, 2, 1], [1, 3, 3, 1], [1, 4, 6, 4, 1]]]
# fmt: on

# if __name__ == "__main__":
#     app = Solution()
#     for test_case, correct_result in zip(test_cases, results):
#         my_result = app.twoSum(test_case)
#         assert (
#             my_result == correct_result
#         ), f"My result: {my_result}, correct result: {correct_result}\nTest Case: {test_case}"
