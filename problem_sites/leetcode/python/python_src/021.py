"""
Merge two sorted linked lists and return it as a new list. The new list should be made by splicing together the nodes of the first two lists.

https://leetcode.com/problems/merge-two-sorted-lists/
"""

from typing import Optional

# Definition for singly-linked list.
class ListNode:
    def __init__(self, x):
        self.val = x
        self.next = None

    def __repr__(self):
        return_list = []
        listnode = self
        while listnode.next is not None:
            return_list.append(listnode.val)
            listnode = listnode.next
        return_list.append(listnode.val)
        return str(return_list)


class Solution:
    def mergeTwoLists(self, l1: ListNode, l2: ListNode) -> Optional[ListNode]:
        if not l1 and not l2:
            return
        if l1 and not l2 or l1 and l1.val < l2.val:
            cur = ListNode(l1.val)
            l1 = l1.next
        else:
            cur = ListNode(l2.val)
            l2 = l2.next

        head = cur
        while l1 or l2:
            if l1 and l2:
                if l1.val < l2.val:
                    cur.next = ListNode(l1.val)
                    cur = cur.next
                    l1 = l1.next
                else:
                    cur.next = ListNode(l2.val)
                    cur = cur.next
                    l2 = l2.next
            elif l1:
                while l1:
                    cur.next = ListNode(l1.val)
                    cur = cur.next
                    l1 = l1.next
            elif l2:
                while l2:
                    cur.next = ListNode(l2.val)
                    cur = cur.next
                    l2 = l2.next
        return head


# Input: 1->2->4, 1->3->4
# Output: 1->1->2->3->4->4
#
# l1 = ListNode(1)
# l1.next = ListNode(2)
# l1.next.next = ListNode(4)
#
# l2 = ListNode(1)
# l2.next = ListNode(3)
# l2.next.next = ListNode(4)
#
# l3 = ListNode(1)
# l3.next = ListNode(1)
# l3.next.next = ListNode(2)
# l3.next.next.next = ListNode(3)
# l3.next.next.next.next = ListNode(4)
# l3.next.next.next.next.next = ListNode(4)
#
# test_cases = [[ListNode(None), ListNode(0)], [l1, l2]]
# results = [ListNode(0), l3]
#
# if __name__ == "__main__":
#     app = Solution()
#     for test_case, correct_result in zip(test_cases, results):
#         my_solution = app.mergeTwoLists(*test_case)
#         print(repr(my_solution))
#         assert repr(my_solution) == repr(
#             correct_result
#         ), f"My result: {app.mergeTwoLists(*test_case)}, correct result: {correct_result}"
