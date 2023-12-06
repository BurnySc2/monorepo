"""
https://leetcode.com/problems/remove-nth-node-from-end-of-list/

https://leetcode.com/problems/remove-nth-node-from-end-of-list/
"""

# Definition for singly-linked list.
class ListNode:
    def __init__(self, x):
        self.val = x
        self.next = None


bro1 = ListNode(1)
bro2 = ListNode(2)
bro3 = ListNode(3)
# Chain bro tham cmonBruh
bro1.next = bro2
bro2.next = bro3
# Now their chained, bro1.next.next is bro3, bro
current = bro1
while current.next:
    print(current.val)
    current = current.next
# Your task is to unchain tham
bro1.next.next = None
# This just removed the third item or so idk, o i just understood the broplem, Nth from the end omg how to read
print("printingg again team")
current = bro1
while current.next:
    print(current.val)
    current = current.next
# see now it printed one less team


class Solution:
    def removeNthFromEnd(self, head: ListNode, n: int) -> ListNode:
        cur = head
        list_bro = [head]
        while cur:
            list_bro.append(cur)
            cur = cur.next
        target = -n - 1
        if len(list_bro) + target == 0:
            return head.next
        list_bro[target].next = list_bro[target].next.next
        return head


#
# class Solution:
#     def removeNthFromEnd(self, head: ListNode, n: int) -> ListNode:
#         cur = head
#         length = 0
#         while cur.next:
#             length += 1
#             cur = cur.next
#         if length < 1:
#             return None
#         cur = head
#         if length - n + 1 == 0:
#             return cur.next
#         for i in range(length-n):
#             cur = cur.next
#         cur.next = cur.next.next
#         return head
