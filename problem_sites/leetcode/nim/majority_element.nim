# 169
# https://leetcode.com/problems/majority-element/
# nim js -d:release -o:majority_element_js.js majority_element.nim
# nim js -d:danger -o:majority_element_js.js majority_element.nim

import tables

proc majorityElement(nums: seq[int]): int {.exportc.} =
    let cache = newTable[int, int]()
    for i in nums:
        let count = cache.getOrDefault(i, 0) + 1
        if count > nums.len div 2:
            return i
        cache[i] = count
