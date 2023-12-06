"""
Given a binary tree, check whether it is a mirror of itself (ie, symmetric around its center).

https://leetcode.com/problems/symmetric-tree/
"""
from typing import Optional

# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left: "TreeNode" = None, right: "TreeNode" = None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def isSymmetric(self, root: Optional[TreeNode]) -> bool:
        def compare_trees(left: Optional[TreeNode], right: Optional[TreeNode]) -> bool:
            if left is None and right is None:
                return True
            if left is None or right is None:
                return False
            if left.val != right.val:
                return False
            return all([compare_trees(left.left, right.right), compare_trees(left.right, right.left),])

        if root is None:
            return True
        return compare_trees(root.left, root.right)


test_tree = TreeNode(1, TreeNode(2, TreeNode(3), TreeNode(4)), TreeNode(2, TreeNode(4), TreeNode(3)))
test_cases = [test_tree]
results = [True]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        assert (
            app.isSymmetric(test_case) == correct_result
        ), f"My result: {app.isSymmetric(test_case)}, correct result: {correct_result}\nTest Case: {test_case}"
