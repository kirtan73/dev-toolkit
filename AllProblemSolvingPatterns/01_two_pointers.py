"""
Two Pointers Pattern (Basic)
----------------------------
Concept:
- Use two indices ("pointers") that move through a sequence in a
  coordinated way instead of using nested loops.
- Often reduces time complexity from O(n^2) to O(n) with O(1) space.

Common variants:
- Pointers starting at opposite ends of a sorted list and moving inward.
- Slow and fast pointers moving through a sequence.

Example: reverse an array in-place
----------------------------------
Goal:
- Input:  [1, 2, 3, 4, 5]
- Output: [5, 4, 3, 2, 1]

Step-by-step (debugger-style):
- Start: left = 0, right = 4, arr = [1, 2, 3, 4, 5]
- Step 1: swap arr[0] and arr[4] -> [5, 2, 3, 4, 1]
         move: left = 1, right = 3
- Step 2: swap arr[1] and arr[3] -> [5, 4, 3, 2, 1]
         move: left = 2, right = 2
- Stop:   left >= right, array is now reversed.

Time Complexity:
- O(n)  (each element is visited at most once).

Space Complexity:
- O(1) extra space (in-place swaps only).
"""

from __future__ import annotations
from typing import List


def reverse_in_place(arr: List[int]) -> None:
    """
    Reverse the list `arr` in-place using the two pointers pattern.

    This modifies the input list directly and returns None.
    """
    left, right = 0, len(arr) - 1

    while left < right:
        # Swap the elements at the two pointers.
        arr[left], arr[right] = arr[right], arr[left]

        # Move the pointers towards the center.
        left += 1
        right -= 1


if __name__ == "__main__":
    nums = [1, 2, 3, 4, 5]
    reverse_in_place(nums)
    # Expected: [5, 4, 3, 2, 1]
    print(f"Reversed array using two pointers: {nums}")
