"""
Given a non-negative integer numRows, generate the first numRows of Pascal's triangle.

https://leetcode.com/problems/pascals-triangle/
"""
from typing import List, Tuple


class ListNode:
    def __init__(self, val: int = 0, next: "ListNode" = None):
        self.val = val
        self.next = next

    def __eq__(self, other: "ListNode") -> bool:
        if not isinstance(other, ListNode):
            return False

        if self.length(self) != self.length(other):
            return False

        first, second = self, other
        while first and second:
            if first.val != second.val:
                return False
            first, second = first.next, second.next
        return True

    def __repr__(self) -> str:
        seen = set()
        nodes = []
        current = self
        while 1:
            if id(current) in seen:
                return "REPEATED NODES " + " -> ".join(map(str, nodes))
            seen.add(id(current))
            nodes.append(current.val)
            if not current.next:
                return " -> ".join(map(str, nodes))
            current = current.next

    @classmethod
    def length(cls, node: "ListNode") -> int:
        l = 0
        start = node
        while start:
            start = start.next
            l += 1
        return l

    @classmethod
    def from_list(cls, my_list: List[int]) -> "ListNode":
        assert my_list
        start = cls(my_list[0])
        cur = start
        for i in my_list[1:]:
            cur.next = cls(i)
            cur = cur.next
        return start


class Solution:
    def reverseKGroup(self, head: ListNode, k: int) -> ListNode:
        if k < 2:
            return head

        first_call = True
        node = head
        for i in range(0, self.length(head) // k):
            if first_call:
                first_call = False
                first, second = self.reverse_k(node, k)
                head = first
                node = second
            else:
                first, second = self.reverse_k(node.next, k)
                node.next = first
                node = second
            # print(f"head: {head}")
            # print(f"node: {node}")
            # print(f"first: {first}")
            # print(f"second: {second}")
            # print()
        return head

    def reverse_k(self, head: ListNode, k: int) -> Tuple[ListNode, ListNode]:
        """ Return the new start of listnode and last element that was reverted """
        start = head
        first = head
        second = first.next
        first.next = None
        third = second.next
        while k > 1:
            second.next = first
            if third is None:
                first, second = second, third
            else:
                first, second, third = second, third, third.next
            k -= 1
        start.next = second
        return first, start

    @classmethod
    def length(cls, node: "ListNode") -> int:
        l = 0
        start = node
        while start:
            start = start.next
            l += 1
        return l


if __name__ == "__main__":
    # fmt: off
    test_cases = [
        [ListNode.from_list([1, 2, 3, 4, 5]), 3],
        [ListNode.from_list([1, 2, 3, 4, 5, 6]), 3],
        [ListNode.from_list([1, 2, 3, 4, 5, 6]), 2],
    ]
    results = [
        ListNode.from_list([3, 2, 1, 4, 5]),
        ListNode.from_list([3, 2, 1, 6, 5, 4]),
        ListNode.from_list([2, 1, 4, 3, 6, 5]),
    ]
    # fmt: on

    # k = 3
    #
    # a = test_cases[0][0]
    # print(a)

    # b, c = Solution().reverse_k(a, k)
    # print(b)
    # print(c)
    # e, f = Solution().reverse_k(c.next, k)
    # print(e)
    # print(f)
    # c.next = e
    # print(b)

    # b = Solution().reverseKGroup(a, 3)
    # print(b)

    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_result = app.reverseKGroup(*test_case)
        assert (
            my_result == correct_result
        ), f"My result: {my_result}, correct result: {correct_result}\nTest Case: {test_case}"
