pub struct Solution {}

use std::i32;
impl Solution {
    pub fn three_sum_closest(nums: Vec<i32>, target: i32) -> i32 {
        let mut closest = i32::MAX;
        let mut closest_value = 0;
        for (index1, i1) in nums.iter().enumerate() {
            for (index2, i2) in nums.iter().skip(index1 + 1).enumerate() {
                for (index3, i3) in nums.iter().skip(index1 + index2 + 2).enumerate() {
                    let value = i1 + i2 + i3;
                    let result = (target - value).abs();
                    if result < closest {
                        closest = result;
                        closest_value = value;
                    }
                }
            }
        }
        closest_value
    }
}

fn run_01() {
    let solution = Solution::three_sum_closest(vec![-1, 2, 1, -4], 1);
    assert_eq!(solution, 2);
}

fn run_02() {
    let solution = Solution::three_sum_closest(vec![0, 0, 0], 1);
    assert_eq!(solution, 0);
}

#[cfg(test)]
mod tests {
    use super::*;
    #[allow(unused_imports)]
    use test::Bencher;

    #[bench]
    fn bench_run_01(b: &mut Bencher) {
        b.iter(|| run_01());
    }

    #[bench]
    fn bench_run_02(b: &mut Bencher) {
        b.iter(|| run_02());
    }
}
