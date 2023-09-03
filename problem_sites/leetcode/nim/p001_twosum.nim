# https://leetcode.com/problems/two-sum/

# nim c -d:release -o:p001_twosum_speed p001_twosum.nim
# nim c -d:release --opt:size -o:p001_twosum_size p001_twosum.nim
# nim c -o:p001_twosum_d p001_twosum.nim

# nim cpp -d:release -o:p001_twosum_cpp p001_twosum.nim
# nim cpp -d:release --opt:size -o:p001_twosum_cpp_size p001_twosum.nim

# nim js -d:release -o:p001_twosum_js.js p001_twosum.nim
# nim js -d:release --opt:size -o:p001_twosum_js_size.js p001_twosum.nim
# nim js -d:danger -o:p001_twosum_js.js p001_twosum.nim

# nim cpp -d:release --nimcache:temp p001_twosum.nim
# nim c -d:release --nimcache:temp p001_twosum.nim
# nim c --cc:clang -d:release --nimcache:temp p001_twosum.nim

# nim c --asm -d:release --nimcache:temp p001_twosum.nim
# nim c --asm -d:danger --nimcache:temp p001_twosum.nim

# nim c -d:danger --mm:arc -d:useMalloc --nimcache:temp p001_twosum.nim
# nim c -d:danger --mm:none -d:useMalloc --nimcache:temp p001_twosum.nim
# nim c -d:release --nimcache:temp -o:p001_twosum p001_twosum.nim



# Best:
# nim js -d:release -o:p001_twosum_js.js p001_twosum.nim
# nim js -d:danger -o:p001_twosum_js.js p001_twosum.nim


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
