from __future__ import annotations

from collections.abc import Iterable
from typing import Generic, TypeVar

T = TypeVar("T")


class Minheap(Generic[T]):
    def __init__(self) -> None:
        self.heap: list[T] = []

    def __repr__(self) -> str:
        if not self.heap:
            return ""
        parts: list[str] = []
        for i, value in enumerate(self.heap):
            parts.append(f"{value} ")
            if i > 0 and ((i + 1) & i) == 0:
                parts.append("\n")
        return "".join(parts).strip()

    def _parent_index(self, index: int) -> int:
        return (index - 1) // 2

    def _left_child_index(self, index: int) -> int:
        return index * 2 + 1

    def _right_child_index(self, index: int) -> int:
        return index * 2 + 2

    def _get_child(self, parent_index: int, offset: int) -> T | None:
        child_index = parent_index * 2 + 1 + offset
        if child_index < len(self.heap):
            return self.heap[child_index]
        return None

    def is_empty(self) -> bool:
        return len(self.heap) == 0

    def _swap(self, index1: int, index2: int) -> None:
        self.heap[index1], self.heap[index2] = self.heap[index2], self.heap[index1]

    def _move_up(self, index: int) -> None:
        while index > 0:
            parent = self._parent_index(index)
            if self.heap[parent] <= self.heap[index]:  # type: ignore[operator]
                break
            self._swap(parent, index)
            index = parent

    def _move_down(self, index: int) -> None:
        size = len(self.heap)
        while True:
            smallest = index
            left = self._left_child_index(index)
            right = self._right_child_index(index)

            if left < size and self.heap[left] < self.heap[smallest]:  # type: ignore[operator]
                smallest = left
            if right < size and self.heap[right] < self.heap[smallest]:  # type: ignore[operator]
                smallest = right

            if smallest == index:
                break

            self._swap(index, smallest)
            index = smallest

    def insert(self, value: T) -> None:
        self.heap.append(value)
        self._move_up(len(self.heap) - 1)

    def get_min(self) -> T:
        if not self.heap:
            raise IndexError("get_min from empty heap")
        return self.heap[0]

    def delete_min(self) -> None:
        if not self.heap:
            raise IndexError("delete_min from empty heap")
        if len(self.heap) == 1:
            self.heap.pop()
            return
        self.heap[0] = self.heap.pop()
        self._move_down(0)

    def build(self, values: Iterable[T]) -> None:
        self.heap = list(values)
        for i in range(len(self.heap) // 2 - 1, -1, -1):
            self._move_down(i)


if __name__ == "__main__":
    p = Minheap()
    build_list = [1, 2, 3, 4, 5, 6, 7]
    p.build(build_list)
    assert len(p.heap) == 7, "build() function not working as expected"
    for i in build_list:
        assert not p.is_empty(), "Min heap should not be empty"
        value = p.get_min()
        assert value == i, f"Expected {i}, got {value}"
        p.delete_min()
    assert p.is_empty(), "Min heap should be empty"

    p2 = Minheap()
    for v in [3.14, 1.41, 2.71]:
        p2.insert(v)
    assert p2.get_min() == 1.41
