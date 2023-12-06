pub struct Solution {}

impl Solution {
    pub fn title_to_number(s: String) -> i32 {
        let mut result = 0;
        for (i, char) in s.chars().rev().enumerate() {
            result += (char as i32 - 64) * 26i32.pow(i as u32);
        }
        result
    }
}

fn run_01() {
    let solution = Solution::title_to_number("A".to_string());
    assert_eq!(solution, 1);
}

fn run_02() {
    let solution = Solution::title_to_number("AB".to_string());
    assert_eq!(solution, 28);
}

fn run_03() {
    let solution = Solution::title_to_number("ZY".to_string());
    assert_eq!(solution, 701);
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
}
