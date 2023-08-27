# https://leetcode.com/problems/two-sum/

# nim c -d:release -o:twosum_speed twosum.nim
# nim c -d:release --opt:size -o:twosum_size twosum.nim
# nim c -o:twosum_d twosum.nim

# nim cpp -d:release -o:twosum_cpp twosum.nim
# nim cpp -d:release --opt:size -o:twosum_cpp_size twosum.nim

# nim js -d:release -o:twosum_js.js twosum.nim
# nim js -d:release --opt:size -o:twosum_js_size.js twosum.nim
# nim js -d:danger -o:twosum_js.js twosum.nim

# nim cpp -d:release --nimcache:temp twosum.nim
# nim c -d:release --nimcache:temp twosum.nim
# nim c --cc:clang -d:release --nimcache:temp twosum.nim

# nim c --asm -d:release --nimcache:temp twosum.nim
# nim c --asm -d:danger --nimcache:temp twosum.nim

# nim c -d:danger --mm:arc -d:useMalloc --nimcache:temp twosum.nim
# nim c -d:danger --mm:none -d:useMalloc --nimcache:temp twosum.nim
# nim c -d:release --nimcache:temp -o:twosum twosum.nim



# Best:
# nim js -d:release -o:twosum_js.js twosum.nim
# nim js -d:danger -o:twosum_js.js twosum.nim


# import tables
# proc twoSum(nums: seq[int], target: int): seq[int] {.exportc.} =
#     var cache: Table[int, int]
#     for i, number in nums:
#         if target - number in cache:
#             return @[cache[target - number], i]
#         cache[number] = i
#     return @[]

proc twoSum(nums: seq[int], target: int): seq[int] {.exportc.} =
    for i in 1..nums.high:
        for j in 0..<i:
            if nums[i] + nums[j] == target:
                return @[i, j]
    return @[]

# proc twoSum(nums: seq[int], target: int): seq[int] {.exportc.} =
#     var i = 1
#     while i < nums.len:
#         var j = 0
#         while j < i:
#             if nums[i] + nums[j] == target:
#                 return @[i, j]
#             j += 1
#         i += 1
#     return @[]
