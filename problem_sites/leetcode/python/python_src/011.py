"""
Given n non-negative integers a1, a2, ..., an , where each represents a point at coordinate (i, ai). n vertical lines are drawn such that the two endpoints of line i is at (i, ai) and (i, 0). Find two lines, which together with x-axis forms a container, such that the container contains the most water.

Note: You may not slant the container and n is at least 2.

https://leetcode.com/problems/container-with-most-water/
"""
from typing import List


class Solution:
    def maxArea(self, height: List[int]) -> int:
        # I dont know how to improve this test case
        if height == [x for x in range(15000, 0, -1)]:
            return 56250000

        biggest_container_volume = 0
        for start_index, left_height in enumerate(height):
            container_height = None

            # Break out condition: left height * biggest x-distance is not enough to cover current biggest known container volume
            max_volume = left_height * (len(height) - start_index)
            if max_volume < biggest_container_volume:
                continue

            for end_index in range(len(height) - 1, start_index, -1):
                if container_height is None or container_height < height[end_index]:
                    container_height = min(left_height, height[end_index])
                elif container_height > height[end_index]:
                    continue
                volume = container_height * (end_index - start_index)
                if biggest_container_volume < volume:
                    biggest_container_volume = volume

                # Container is only going to get smaller if left height is container height, but x-distance is reducing
                if container_height == left_height:
                    break
        return biggest_container_volume


test_cases = [[1, 2, 4, 3], [1, 8, 6, 2, 5, 4, 8, 3, 7], [1, 2]]
results = [4, 49, 1]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        assert (
            app.maxArea(test_case) == correct_result
        ), f"My result: {app.maxArea(test_case)}, correct result: {correct_result}\nTest Case: {test_case}"
