from typing import List


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def __init__(self):
        self.amount = 0

    def pathSum(self, root: TreeNode, sum: int) -> int:
        self.amount = 0
        self.traverse_tree(root, target=sum)
        return self.amount

    def traverse_tree(self, node: TreeNode, target: int):
        """ Vertical recursive traversal. """
        if node is None:
            return
        self.find_sum_from_node(node, node.val, target)
        if node.val == target:
            self.amount += 1
        self.traverse_tree(node.left, target)
        self.traverse_tree(node.right, target)

    def find_sum_from_node(self, node: TreeNode, current_sum: int, target: int):
        """ Traverses the current node and tries to find all the sums from its leaves. """
        if node is None:
            return
        if node.left:
            if current_sum + node.left.val == target:
                self.amount += 1
                # print(f"Found sum path: {current_sum + [node.left.val]}")
            self.find_sum_from_node(node.left, current_sum + node.left.val, target)
        if node.right:
            if current_sum + node.right.val == target:
                self.amount += 1
                # print(f"Found sum path: {current_sum + [node.right.val]}")
            self.find_sum_from_node(node.right, current_sum + node.right.val, target)


if __name__ == "__main__":
    sol = Solution()
    asd = TreeNode(
        10,
        # Left subtree
        TreeNode(5, TreeNode(3, TreeNode(3), TreeNode(-2)), TreeNode(2, None, TreeNode(1))),
        # Right subtree
        TreeNode(-3, TreeNode(1), TreeNode(11)),
    )
    result = sol.pathSum(asd, 8)
    print(result)

    asd = TreeNode(1)
    result = sol.pathSum(asd, 1)
    print(result)

    asd = TreeNode(1, None, TreeNode(2))
    result = sol.pathSum(asd, 2)
    print(result)

    asd = TreeNode(1, TreeNode(2))
    result = sol.pathSum(asd, 2)
    print(result)
