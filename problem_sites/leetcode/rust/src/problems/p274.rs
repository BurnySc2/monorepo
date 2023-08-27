pub struct Solution {}

use std::collections::HashMap;
use std::i32;

impl Solution {
    pub fn h_index(citations: Vec<i32>) -> i32 {
        let mut map = HashMap::new();
        for i in citations {
            // If entry exists: modify it by adding +1, else insert value
            map.entry(i).and_modify(|e| *e += 1).or_insert(1);
        }
        let mut keys: Vec<_> = map.keys().collect();
        keys.sort();
        keys.reverse();
        let mut min_key = i32::MAX;
        let mut amount = 0;
        for key in keys {
            if amount >= *key {
                return amount.min(min_key);
            }
            if let Some(count) = map.get(&key) {
                amount += count;
                min_key = *key;
            }
        }
        amount.min(min_key)
    }
}

fn run_01() {
    let solution = Solution::h_index(vec![3, 0, 6, 1, 5]);
    assert_eq!(solution, 3);
}

fn run_02() {
    let solution = Solution::h_index(vec![3, 0, 6, 1, 5, 4, 7]);
    assert_eq!(solution, 4);
}

fn run_03() {
    let solution = Solution::h_index(vec![]);
    assert_eq!(solution, 0);
}

fn run_04() {
    let solution = Solution::h_index(vec![1, 2, 2]);
    assert_eq!(solution, 2);
}

fn run_05() {
    let solution = Solution::h_index(vec![4, 4, 0, 0]);
    assert_eq!(solution, 2);
}

fn run_06() {
    let solution = Solution::h_index(vec![1, 7, 9, 4]);
    assert_eq!(solution, 3);
}

fn run_07() {
    let solution = Solution::h_index(vec![1, 1]);
    assert_eq!(solution, 1);
}

fn run_08() {
    let solution = Solution::h_index(vec![2]);
    assert_eq!(solution, 1);
}

fn run_09() {
    let solution = Solution::h_index(vec![2, 3, 2]);
    assert_eq!(solution, 2);
}

fn run_10() {
    let solution = Solution::h_index(vec![1, 2, 2, 2]);
    assert_eq!(solution, 2);
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

    #[bench]
    fn bench_run_03(b: &mut Bencher) {
        b.iter(|| run_03());
    }

    #[bench]
    fn bench_run_04(b: &mut Bencher) {
        b.iter(|| run_04());
    }

    #[bench]
    fn bench_run_05(b: &mut Bencher) {
        b.iter(|| run_05());
    }

    #[bench]
    fn bench_run_06(b: &mut Bencher) {
        b.iter(|| run_06());
    }

    #[bench]
    fn bench_run_07(b: &mut Bencher) {
        b.iter(|| run_07());
    }

    #[bench]
    fn bench_run_08(b: &mut Bencher) {
        b.iter(|| run_08());
    }

    #[bench]
    fn bench_run_09(b: &mut Bencher) {
        b.iter(|| run_09());
    }

    #[bench]
    fn bench_run_10(b: &mut Bencher) {
        b.iter(|| run_10());
    }
}
