from typing import List


class Solution:
    def trap(self, height: List[int]) -> int:
        if not height:
            return 0
        left_index = -1
        right_index = len(height)
        left_height = 0
        right_height = 0
        volume = 0
        while left_index < right_index:
            # Approach from left
            while left_height <= right_height:
                left_index += 1
                if left_index >= len(height) or left_index > right_index:
                    break
                current_height = height[left_index]
                if current_height <= left_height:
                    volume += left_height - current_height
                else:
                    left_height = max(left_height, current_height)
            # Approach from right
            while right_height < left_height:
                right_index -= 1
                if right_index == -1:
                    break
                current_height = height[right_index]
                if current_height <= right_height:
                    volume += right_height - current_height
                else:
                    right_height = max(right_height, current_height)
        return volume


test_cases = [[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1], [2, 0, 2], [5, 5, 1, 7, 1, 1, 5, 2, 7, 6]]
results = [6, 2, 23]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        assert (
            app.trap(test_case) == correct_result
        ), f"My result: {app.trap(test_case)}, correct result: {correct_result}\nTest Case: {test_case}"
