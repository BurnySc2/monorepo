pub struct Solution {}

impl Solution {
    pub fn reverse(x: i32) -> i32 {
        let is_negative = x < 0;
        let a;
        if is_negative {
            a = -x;
        } else {
            a = x;
        }

        // a is now positive, convert to string
        let b: String = a.to_string();
        let mut result: i64 = 0;
        // Loop over string, i is index and c is char
        for (i, c) in b.chars().enumerate() {
            result += (c as i64 - 48) * (10 as i64).pow(i as u32);
            // println!("{0}, {1}, {2:?}, {3}, {4}", c, i, c as i32 - 48, (10 as i64).pow(i as u32), result);
        }

        // println!("{0}, {1}", result, limit);
        let limit = 2i64.pow(31u32);
        if result > limit - 1 || result < -limit {
            return 0;
        }

        if is_negative {
            return -result as i32;
        }
        return result as i32;
    }
}

fn run_007_01() {
    let solution = Solution::reverse(123);
    assert_eq!(solution, 321);
}
fn run_007_02() {
    let solution = Solution::reverse(-123);
    assert_eq!(solution, -321);
}
fn run_007_03() {
    let solution = Solution::reverse(120);
    assert_eq!(solution, 21);
}

#[cfg(test)]
mod tests {
    use super::*;
    #[allow(unused_imports)]
    use test::Bencher;

    // This will only be executed when using "cargo test" and not "cargo bench"
    #[bench]
    fn bench_run_007_01(b: &mut Bencher) {
        b.iter(|| run_007_01());
    }
    #[bench]
    fn bench_run_007_02(b: &mut Bencher) {
        b.iter(|| run_007_02());
    }
    #[bench]
    fn bench_run_007_03(b: &mut Bencher) {
        b.iter(|| run_007_03());
    }
}
