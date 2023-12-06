# 169
# https://leetcode.com/problems/majority-element/
# nim js -d:release -o:p169_majority_element_js.js p169_majority_element.nim
# nim js -d:danger -o:p169_majority_element_js.js p169_majority_element.nim
import tables

proc majorityElement(nums: seq[int]): int {.exportc.} =
    let cache = newTable[int, int]()
    for i in nums:
        let count = cache.getOrDefault(i, 0) + 1
        if count > nums.len div 2:
            return i
        cache[i] = count
