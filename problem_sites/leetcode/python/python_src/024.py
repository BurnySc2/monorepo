"""
Given a linked list, swap every two adjacent nodes and return its head.

You may not modify the values in the list's nodes, only nodes itself may be changed.

https://leetcode.com/problems/swap-nodes-in-pairs/
"""

# Given 1->2->3->4, you should return the list as 2->1->4->3.
# Definition for singly-linked list.

from typing import Generator


class ListNode:
    def __init__(self, val: int, next: "ListNode" = None):
        self.val = val
        self.next = next

    def __iter__(self):
        return self.__next__()

    def __next__(self) -> Generator[int, None, None]:
        current = self
        while current.next:
            yield current.val
            current = current.next
        yield current.val

    def __repr__(self) -> str:
        nodes_values = []
        for node_value in self:
            nodes_values.append(str(node_value))
        return " -> ".join(nodes_values)

    def __eq__(self, other: "ListNode") -> bool:
        if self.length() != other.length():
            return False
        for value_node1, value_node2 in zip(self, other):
            if value_node1 != value_node2:
                return False
        return True

    def length(self) -> int:
        length = 0
        current = self
        while current.next:
            current = current.next
            length += 1
        return length


class Solution:
    def swapPairs(self, head: ListNode) -> ListNode:
        if head is None:
            return
        if head.next is None:
            return head
        new_head = None
        previous = None
        current = head
        while 1:
            # Split list node into 3 parts: first node, second node, tail
            next = current.next
            # Break out for uneven long listnodes
            if next is None:
                break
            tail = next.next
            next.next = current
            current.next = tail
            if new_head is None:
                new_head = next
            if previous is not None:
                previous.next = next
            # If there are no more listnodes: break out
            if tail is None:
                break
            # Start 2 nodes later again
            previous = next.next
            current = previous.next
        return new_head


# TODO
test_node = ListNode(5, ListNode(6, ListNode(7, ListNode(8))))
output_node = ListNode(6, ListNode(5, ListNode(8, ListNode(7))))
test_node2 = ListNode(5, ListNode(6, ListNode(7)))
output_node2 = ListNode(6, ListNode(5, ListNode(7)))
# print(f"My node: {test_node}")
test_cases = [test_node, test_node2]
results = [output_node, output_node2]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        assert (
            app.swapPairs(test_case) == correct_result
        ), f"My result: {app.swapPairs(test_case)}, correct result: {correct_result}"
