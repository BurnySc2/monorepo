# NOT SOLVED! Memory limit exceeded
import sys


class Tree:
    def __init__(self, value: int) -> None:
        self.value = value
        self.children: list[Tree] = []  # noqa: UP006

    def add_child(self, value: int) -> None:
        smallest = 10**4
        for child in self.children:
            if child.value < value:
                child.add_child(value)
            if child.value < smallest:
                smallest = child.value
        if len(self.children) > 0 and value < smallest and self.value < value:
            self.children.append(Tree(value))
        if len(self.children) == 0 and self.value < value:
            self.children.append(Tree(value))

    @property
    def depth(self) -> int:
        return max([child.depth + 1 for child in self.children], default=1)

    def __repr__(self) -> str:
        if len(self.children) == 0:
            return f"{self.value}"
        children = ",".join(f"{child}" for child in self.children)
        return f"{self.value}({children})"


class Solution:
    def lengthOfLIS(self, nums: list[int]) -> int:  # noqa: N802, UP006
        if len(nums) == 1:
            return 1
        trees = []
        current_minimum = sys.maxsize
        for value in nums:
            for tree in trees:
                tree.add_child(value)
            if value < current_minimum:
                trees.append(Tree(value=value))
                current_minimum = value
        # print(f"{trees}")
        return max([tree.depth for tree in trees], default=1)


if __name__ == "__main__":
    s = Solution()

    case1 = [10, 9, 2, 5, 3, 7, 101, 18]
    expected1 = 4
    calculated1 = s.lengthOfLIS(case1)
    assert expected1 == calculated1, (expected1, calculated1)

    case2 = [4, 10, 4, 3, 8, 9]
    expected2 = 3
    calculated2 = s.lengthOfLIS(case2)
    assert expected2 == calculated2, (expected2, calculated2)
