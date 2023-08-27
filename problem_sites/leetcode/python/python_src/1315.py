# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def sumEvenGrandparent(self, root: TreeNode) -> int:
        if not root:
            return 0

        if root.val % 2 == 0:
            if root.left is not None:
                root.left.has_even_parent = True
            if root.right is not None:
                root.right.has_even_parent = True

        if hasattr(root, "has_even_parent"):
            if root.left is not None:
                root.left.has_even_grand_parent = True
            if root.right is not None:
                root.right.has_even_grand_parent = True

        value = 0
        if hasattr(root, "has_even_grand_parent"):
            value = root.val

        return value + self.sumEvenGrandparent(root.left) + self.sumEvenGrandparent(root.right)
