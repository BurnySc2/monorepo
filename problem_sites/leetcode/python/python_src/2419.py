class Solution:
    def longestSubarray(self, nums: list[int]) -> int:
        largest_number = 0
        longest_sequence = 0
        current_sequence = 0
        for i in nums:
            if i == largest_number:
                current_sequence += 1
            elif i > largest_number:
                largest_number = i
                longest_sequence = 0
                current_sequence = 1
            else:
                longest_sequence = max(longest_sequence, current_sequence)
                current_sequence = 0
        return max(longest_sequence, current_sequence)
