pub struct Solution {}

impl Solution {
    pub fn is_palindrome(x: i32) -> bool {
        if x < 0 {
            return false;
        }
        let mut number = x;
        let mut reverse_number = 0;
        while number > 0 {
            let remainder = number % 10;
            number = number / 10;
            reverse_number = reverse_number * 10 + remainder;
        }
        return reverse_number == x;
    }
}

fn run_009_01() {
    let solution = Solution::is_palindrome(121);
    assert_eq!(solution, true);
}
fn run_009_02() {
    let solution = Solution::is_palindrome(-123);
    assert_eq!(solution, false);
}
fn run_009_03() {
    let solution = Solution::is_palindrome(10);
    assert_eq!(solution, false);
}

#[cfg(test)]
mod tests {
    use super::*;
    #[allow(unused_imports)]
    use test::Bencher;

    #[bench]
    fn bench_run_009_01(b: &mut Bencher) {
        b.iter(|| run_009_01());
    }
    #[bench]
    fn bench_run_009_02(b: &mut Bencher) {
        b.iter(|| run_009_02());
    }
    #[bench]
    fn bench_run_009_03(b: &mut Bencher) {
        b.iter(|| run_009_03());
    }
}
