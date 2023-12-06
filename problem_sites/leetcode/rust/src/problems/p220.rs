pub struct Solution {}

use std::collections::HashSet;
impl Solution {
    pub fn contains_nearby_almost_duplicate(nums: Vec<i32>, k: i32, t: i32) -> bool {
        if t == 0 {
            let my_set: HashSet<i32> = nums.iter().cloned().collect();
            if my_set.len() == nums.len() {
                return false;
            }
        }

        for (i, val1) in nums.iter().enumerate() {
            for (j, val2) in nums.iter().enumerate().skip(i + 1) {
                if j - i > k as usize {
                    break;
                }
                if (*val1 as i64 - *val2 as i64).abs() > t as i64 {
                    continue;
                }
                return true;
            }
        }
        false
    }
}

fn run_01() {
    let v = vec![1, 2, 3, 1];
    let k = 3;
    let t = 1;
    let solution = Solution::contains_nearby_almost_duplicate(v, k, t);
    assert_eq!(solution, true);
}

fn run_02() {
    let v = vec![1, 5, 9, 1, 5, 9];
    let k = 2;
    let t = 3;
    let solution = Solution::contains_nearby_almost_duplicate(v, k, t);
    assert_eq!(solution, false);
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
