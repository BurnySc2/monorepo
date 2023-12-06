from string import ascii_lowercase, ascii_uppercase, digits
from heapq import heapify, heappush, heappop
from typing import List


class Solution:

    def strongPasswordChecker(self, password: str) -> int:
        previous_letters: List[str] = []
        # Groups of same-letters
        repeated_letters: List[int] = []

        # Analyse password
        has_lowercase = False
        has_uppercase = False
        has_digit = False
        for letter in password:
            if not has_lowercase and letter in ascii_lowercase:
                has_lowercase = True
            elif not has_uppercase and letter in ascii_uppercase:
                has_uppercase = True
            elif not has_digit and letter in digits:
                has_digit = True

            if previous_letters and previous_letters[0] != letter:
                if len(previous_letters) >= 3:
                    repeated_letters.append(len(previous_letters))
                previous_letters.clear()
            previous_letters.append(letter)
        # Same as above but outside the for loop
        if previous_letters and len(previous_letters) >= 3:
            repeated_letters.append(len(previous_letters))

        # Change password and count changes
        pw_length = len(password)
        remove_operations = self.handle_repeated_letters_to_reduce_pw_length(repeated_letters, pw_length)
        add_operations = self.handle_repeated_letters_to_increase_pw_length(repeated_letters, pw_length)
        edit_operations = self.handle_remaining_repeated_letters(repeated_letters)
        min_edit_add_operations_required = [has_lowercase, has_uppercase, has_digit].count(False)

        return remove_operations + max(min_edit_add_operations_required, add_operations + edit_operations)

    def handle_repeated_letters_to_reduce_pw_length(self, repeated_letters: List[int], pw_length: int) -> int:
        operations = 0
        if pw_length <= 20:
            return operations

        # Get repeated_letters length to mod 3 == 2, starting from mod 3 == 0
        to_remove_indices = []
        for index, value in enumerate(repeated_letters):
            if value % 3 == 0:
                if value == 3:
                    to_remove_indices.insert(0, index)
                else:
                    repeated_letters[index] -= 1
                operations += 1
                pw_length -= 1
                if pw_length <= 20:
                    break
        # Remove at highest index first
        for index in to_remove_indices:
            del repeated_letters[index]

        # Get repeated_letters length to mod 3 == 2, starting from mod 3 in [0, 1]
        did_changes = True
        while pw_length > 20 and did_changes:
            did_changes = False
            for index, value in enumerate(repeated_letters):
                if value % 3 in [0, 1]:
                    if value == 3:
                        del repeated_letters[index]
                    else:
                        repeated_letters[index] -= 1
                    operations += 1
                    pw_length -= 1
                    did_changes = True
                    break

        # Remove letters from smallest repeated group first
        heapify(repeated_letters)
        while repeated_letters and pw_length > 20:
            heap_item = heappop(repeated_letters)
            operations += 1
            pw_length -= 1
            if heap_item > 3:
                heappush(repeated_letters, heap_item - 1)

        # While we have no more repeated groups, keep removing characters
        while pw_length > 20:
            operations += 1
            pw_length -= 1

        return operations

    def handle_repeated_letters_to_increase_pw_length(self, repeated_letters: List[int], pw_length: int) -> int:
        operations = 0
        while pw_length < 6:
            if repeated_letters:
                if repeated_letters[0] < 5:
                    del repeated_letters[0]
                else:
                    repeated_letters[0] -= 2
            operations += 1
            pw_length += 1

        return operations

    def handle_remaining_repeated_letters(self, repeated_letters: List[int]) -> int:
        operations = 0

        while repeated_letters:
            if repeated_letters[0] < 6:
                del repeated_letters[0]
            else:
                repeated_letters[0] -= 3
            operations += 1
        return operations


if __name__ == '__main__':
    test_cases_and_results = [
        ["aaaabbaaabbaaa123456A", 3],
        ["ABABABABABABABABABAB1", 2],
        ["aaaabbbbccccddeeddeeddeedd", 8],
        ["bbaaaaaaaaaaaaaaacccccc", 8],
        ["aaa", 3],
        ["1111111111", 3],
    ]
    app = Solution()
    for (test_case, correct_result) in test_cases_and_results:
        my_result = app.strongPasswordChecker(test_case)
        assert (
            my_result == correct_result
        ), f"My result: {my_result}, correct result: {correct_result}\nTest Case: {test_case}"
