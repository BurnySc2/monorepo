# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def post_order_traversal(node: TreeNode | None):
    if node is None:
        return
    if node.right is not None:
        yield from post_order_traversal(node.right)
    yield node
    if node.left is not None:
        yield from post_order_traversal(node.left)


class Solution:
    def bstToGst(self, root: TreeNode | None) -> TreeNode | None:
        current_sum = 0
        for node in post_order_traversal(root):
            current_sum, node.val = node.val + current_sum, node.val + current_sum
        return root
