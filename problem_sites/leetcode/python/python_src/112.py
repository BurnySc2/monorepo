"""
Given a binary tree, check whether it is a mirror of itself (ie, symmetric around its center).

https://leetcode.com/problems/symmetric-tree/
"""


# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def hasPathSum(self, root: TreeNode, targetSum: int, current_sum=0) -> bool:
        if not root:
            return False

        if not root.left and not root.right:
            return targetSum == current_sum + root.val

        if root.left:
            if self.hasPathSum(root.left, targetSum, current_sum + root.val):
                return True

        if root.right:
            if self.hasPathSum(root.right, targetSum, current_sum + root.val):
                return True

        return False

a = {1, 2, 3, "dein gesuchtes"}
if "dein gesuchtes" in a:
    print("yolo")



# test_tree = TreeNode(1, TreeNode(2, TreeNode(3), TreeNode(4)), TreeNode(2, TreeNode(4), TreeNode(3)))
# test_cases = [test_tree]
# results = [True]
#
# if __name__ == "__main__":
#     app = Solution()
#     for test_case, correct_result in zip(test_cases, results):
#         assert (
#             app.hasPathSum(test_case) == correct_result
#         ), f"My result: {app.hasPathSum(test_case)}, correct result: {correct_result}\nTest Case: {test_case}"
