"""
Linear Search (Sequential Search)
---------------------------------
Concept:
- Scan each element in a list one by one until the target is found
  or the list ends.
- Works on **any** list (no need for sorting), but can be slow on
  large inputs because every element may need to be checked.

When to use:
- Small lists or when performance is not critical.
- Lists that are not sorted and cannot be easily sorted.
- Quick, brute-force baseline before optimizing.

Step-by-step example (debugger-style):
- Input array: [4, 2, 9, 7], target = 9
- i = 0 -> arr[0] = 4  != 9  -> continue
- i = 1 -> arr[1] = 2  != 9  -> continue
- i = 2 -> arr[2] = 9  == 9  -> return 2 (index where target is found)
- Loop stops as soon as the target is found.

Time Complexity:
- Worst case: O(n)  (target not found or at the last position)
- Best case:  O(1)  (target at the first position)
- Average:    O(n)

Space Complexity:
- O(1) extra space (we only use a few variables regardless of input size).
"""

from __future__ import annotations
from typing import List, Any, Optional


def linear_search(arr: List[Any], target: Any) -> Optional[int]:
    """
    Return the index of `target` in `arr` using linear search.
    If the target is not found, return None.
    """
    for index, value in enumerate(arr):
        # Check the current element against the target.
        if value == target:
            return index  # Found the target at this index.
    # If we finish the loop, the target does not exist in the list.
    return None


if __name__ == "__main__":
    data = [4, 2, 9, 7]
    target_value = 9

    # Expected: index 2 (0-based) because data[2] == 9.
    result = linear_search(data, target_value)
    if result:
        print(f"Found element {target_value} at index {result}.")
    else:
        print(f"Element {target_value} not found in the list.")
