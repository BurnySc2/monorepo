import math
import tables

proc mean[T](nums: seq[T]): float =
    ## Average
    assert nums.len > 0
    nums.sum / nums.len
when isMainModule:
    assert 2'f == @[1, 2, 3].mean, $ @[1, 2, 3].mean

proc median[T](nums: seq[T]): float =
    ## Middle value
    assert nums.len > 0
    let center = nums.len div 2
    if nums.len mod 2 == 0:
        return (nums[center - 1] + nums[center]) / 2
    return nums[center].float
when isMainModule:
    assert 2 == @[1, 2, 3].median, $ @[1, 2, 3].median
    assert 2.5 == @[1, 2, 3, 4].median, $ @[1, 2, 3, 4].median

proc mode[T](nums: seq[T]): T =
    ## Most occuring value
    assert nums.len > 0
    let countTable = newCountTable(nums)
    return countTable.largest.key
when isMainModule:
    assert 2 == @[1, 2, 2, 3].mode, $ @[1, 2, 2, 3].mode
    assert 2 == @[1, 2, 2, 2, 3].mode, $ @[1, 2, 2, 2, 3].mode
    assert 1 == @[1, 1, 2, 3].mode, $ @[1, 1, 2, 3].mode
    assert 3 == @[1, 2, 3, 3].mode, $ @[1, 2, 3, 3].mode

proc mae[T](nums: seq[T]): float =
    ## Mean absolute error
    assert nums.len > 0
    let meanValue = nums.mean
    for i in nums:
        result += (i.float - meanValue).abs
    result /= nums.len.float
when isMainModule:
    assert 2 / 3 == @[1, 2, 3].mae, $ @[1, 2, 3].mae
    assert 1.2 == @[1, 2, 3, 4, 5].mae, $ @[1, 2, 3, 4, 5].mae

proc mse[T](nums: seq[T]): float =
    ## Mean squared error
    assert nums.len > 0
    let meanValue = nums.mean
    for i in nums:
        result += (i.float - meanValue)^2
    result /= nums.len.float
when isMainModule:
    assert 2 / 3 == @[1, 2, 3].mse, $ @[1, 2, 3].mse
    assert 2 == @[1, 2, 3, 4, 5].mse, $ @[1, 2, 3, 4, 5].mse

proc rmse[T](nums: seq[T]): float =
    ## Root mean squared error
    assert nums.len > 0
    nums.mse.sqrt
when isMainModule:
    assert (2 / 3).sqrt == @[1, 2, 3].rmse, $ @[1, 2, 3].rmse
    assert 2.0.sqrt == @[1, 2, 3, 4, 5].rmse, $ @[1, 2, 3, 4, 5].rmse

# variance of distribution
# generate sample of distribution (with size)

# calc regression of distribution

# plot?
# ecdf
# box plot
# violin box

# bewertung eines models
# accuracy of model
# precision of model
# recall of model
# f1 score of model



