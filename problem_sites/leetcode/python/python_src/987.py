from heapq import heappop

# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val: int = 0, left: "TreeNode" = None, right: "TreeNode" = None):
        self.val = val
        self.left = left
        self.right = right


from typing import List, DefaultDict
from collections import defaultdict


class Solution:
    def verticalTraversal(self, root: TreeNode) -> List[List[int]]:
        my_dict = defaultdict(list)
        my_dict[0] = []
        self.verticalTraversal2([root], [0], my_dict)
        results = []
        for i in sorted(my_dict.keys()):
            results.append(my_dict[i])
        return results

    def verticalTraversal2(self, nodes: List[TreeNode], x_values: List[int], my_dict: DefaultDict[int, List[int]]):
        new_nodes = []
        new_x_values = []
        row = defaultdict(list)

        a_node_isnt_none = False

        for x_value, node in zip(x_values, nodes):
            new_x_values.append(x_value - 1)
            new_x_values.append(x_value + 1)
            if node is None:
                new_nodes.append(None)
                new_nodes.append(None)
                continue
            a_node_isnt_none = True
            row[x_value].append(node.val)
            new_nodes.append(node.left)
            new_nodes.append(node.right)

        # Sort values if x values overlap
        for key in sorted(row.keys()):
            for value in sorted(row[key]):
                my_dict[key].append(value)

        # Recursion, stop recursion if a node was None
        if a_node_isnt_none:
            self.verticalTraversal2(new_nodes, new_x_values, my_dict)


if __name__ == "__main__":
    sol = Solution()
    asd = TreeNode(1, TreeNode(2, TreeNode(4), TreeNode(5)), TreeNode(3, TreeNode(6), TreeNode(7)))
    result = sol.verticalTraversal(asd)
    print(result)

    asd = TreeNode(0, None, TreeNode(1, TreeNode(2)))
    result = sol.verticalTraversal(asd)
    print(result)
