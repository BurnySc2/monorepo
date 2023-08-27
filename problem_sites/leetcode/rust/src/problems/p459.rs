pub struct Solution {}

impl Solution {
    pub fn repeated_substring_pattern(s: String) -> bool {
        for right in 1..(s.len() / 2 + 1) {
            if s.len() % right != 0 {
                continue;
            }
            let word = &s[0..right];
            let times = s.len() / word.len();
            if word.repeat(times) == s {
                return true;
            }
        }
        false
    }
}

fn run_01() {
    let s = "abab".to_string();
    let r = Solution::repeated_substring_pattern(s);
    assert_eq!(r, true);
}

fn run_02() {
    let s = "abab".to_string();
    let r = Solution::repeated_substring_pattern(s);
    assert_eq!(r, true);
}

fn run_03() {
    let s = "abcabcabcabc".to_string();
    let r = Solution::repeated_substring_pattern(s);
    assert_eq!(r, true);
}

fn run_04() {
    let s = "ababba".to_string();
    let r = Solution::repeated_substring_pattern(s);
    assert_eq!(r, false);
}

fn run_05() {
    let s = "aba".to_string();
    let r = Solution::repeated_substring_pattern(s);
    assert_eq!(r, false);
}

fn run_06() {
    let s = "abac".to_string();
    let r = Solution::repeated_substring_pattern(s);
    assert_eq!(r, false);
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
}
