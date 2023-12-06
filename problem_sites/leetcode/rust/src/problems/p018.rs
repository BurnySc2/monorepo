pub struct Solution {}

use std::collections::HashSet;

impl Solution {
    pub fn four_sum(nums: Vec<i32>, target: i32) -> Vec<Vec<i32>> {
        // Using hashset to avoid duplicates
        let mut solution_set: HashSet<Vec<i32>> = HashSet::new();
        let mut nums_sorted = nums.clone();
        nums_sorted.sort();

        for (index1, i1) in nums_sorted.iter().enumerate() {
            for (index2, i2) in nums_sorted.iter().skip(index1 + 1).enumerate() {
                for (index3, i3) in nums_sorted.iter().skip(index1 + index2 + 2).enumerate() {
                    for i4 in nums_sorted.iter().skip(index1 + index2 + index3 + 3) {
                        let value = i1 + i2 + i3 + i4;
                        if value > target {
                            break;
                        } else if value == target {
                            solution_set.insert(vec![*i1, *i2, *i3, *i4]);
                        }
                    }
                }
            }
        }
        let solution: Vec<Vec<_>> = solution_set.into_iter().collect();
        solution
    }
}

fn run_01() {
    let solution = Solution::four_sum(vec![1, 0, -1, 0, -2, 2], 0);
    let mut result = vec![];
    result.push(vec![-1, 0, 0, 1]);
    result.push(vec![-2, -1, 1, 2]);
    result.push(vec![-2, 0, 0, 2]);
    assert_eq!(solution, result);
}

fn run_02() {
    let solution = Solution::four_sum(vec![1, -2, -5, -4, -3, 3, 3, 5], -11);
    let mut result = vec![];
    result.push(vec![-5, -4, -3, 1]);
    assert_eq!(solution, result);
}

#[cfg(test)]
mod tests {
    use super::*;
    #[allow(unused_imports)]
    use test::Bencher;

    // #[bench]
    // fn bench_run_01(b: &mut Bencher) {
    //     b.iter(|| run_01());
    // }

    #[bench]
    fn bench_run_02(b: &mut Bencher) {
        b.iter(|| run_02());
    }
}
