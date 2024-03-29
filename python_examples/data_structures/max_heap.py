from __future__ import annotations

import math

# [
#     1,
#     2, 3,
#     4, 5, 6, 7,
# ]


class MaxHeap:
    def __init__(self):
        self.tree: list[int] = [0]

    def __repr__(self):
        return_list = []
        multiples_of_two = {2**n for n in range(1, 1 + int(math.log(len(self.tree), 2)))}
        for index, value in enumerate(self.tree[1:], start=1):
            if index in multiples_of_two:
                return_list.append("\n")
            return_list.append(value)
            return_list.append(" ")
        return "".join(str(x) for x in return_list)

    def pop(self):
        if len(self.tree) < 2:
            raise IndexError("cant pop empty heap")
        return_value = self.tree[1]
        if len(self.tree) > 2:
            self.tree[1] = self.tree[-1]
            self._move_down(1)
        self.tree.pop()
        return return_value

    def insert(self, value: int):
        index = len(self.tree)
        self.tree.append(value)
        self._move_up(index)

    @classmethod
    def _get_parent(cls, index: int) -> int:
        if index < 2:
            raise IndexError("root node has no parents")
        return index // 2

    @classmethod
    def _get_children(cls, index: int) -> list[int]:
        times_two = index * 2
        return [times_two, times_two + 1]

    def _move_up(self, index: int):
        if index < 2:
            return
        parent = self._get_parent(index)
        if self.tree[parent] < self.tree[index]:
            # Swap node and parent
            self.tree[parent], self.tree[index] = self.tree[index], self.tree[parent]
            self._move_up(parent)

    def _move_down(self, index: int):
        child1, child2 = self._get_children(index)
        max_index = len(self.tree) - 1

        if child1 > max_index:
            return
        swap_child = child1 if child2 > max_index else max(child1, child2, key=lambda x: self.tree[x])

        # Swap current element with the biggest child
        if self.tree[swap_child] > self.tree[index]:
            self.tree[swap_child], self.tree[index] = self.tree[index], self.tree[swap_child]
            self._move_down(swap_child)


if __name__ == "__main__":
    m = MaxHeap()
    for i in range(1, 8):
        m.insert(i)

    for i in range(7, 0, -1):
        print(m)
        my_value = m.pop()
        assert i == my_value, f"Expected {i}, got {my_value}"

    print(m)
