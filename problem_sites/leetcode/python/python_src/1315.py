# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val: int = 0, left: "TreeNode | None" = None, right: "TreeNode | None" = None) -> None:
        self.val: int = val
        self.left: TreeNode | None = left
        self.right: TreeNode | None = right


class Solution:
    def sumEvenGrandparent(self, root: TreeNode | None) -> int:
        if not root:
            return 0

        if root.val % 2 == 0:
            if root.left is not None:
                root.left.has_even_parent = True  # pyrefly: ignore[missing-attribute]
            if root.right is not None:
                root.right.has_even_parent = True  # pyrefly: ignore[missing-attribute]

        if hasattr(root, "has_even_parent"):
            if root.left is not None:
                root.left.has_even_grand_parent = True  # pyrefly: ignore[missing-attribute]
            if root.right is not None:
                root.right.has_even_grand_parent = True  # pyrefly: ignore[missing-attribute]

        value = 0
        if hasattr(root, "has_even_grand_parent"):
            value = root.val

        return value + self.sumEvenGrandparent(root.left) + self.sumEvenGrandparent(root.right)
