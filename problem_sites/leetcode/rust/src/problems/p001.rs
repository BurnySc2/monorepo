pub struct Solution {}

impl Solution {
    pub fn two_sum(nums: Vec<i32>, target: i32) -> Vec<i32> {
        for (i, value1) in nums.iter().enumerate() {
            for j in (i + 1)..nums.len() {
                if value1 + nums[j] == target {
                    return vec![i as i32, j as i32];
                }
            }
        }
        return vec![];
    }
}

fn run_01() {
    let solution = Solution::two_sum(vec![13, 16, 2, 7, 11, 15], 9);
    assert_eq!(solution, vec![2, 3]);
}

fn run_02() {
    let solution = Solution::two_sum(vec![2, 7, 11, 15], 9);
    assert_eq!(solution, vec![0, 1]);
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
