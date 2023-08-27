use std::collections::{HashSet, VecDeque};

pub struct Solution {}

impl Solution {
    // VecDeque + HashSet solution
    pub fn length_of_longest_substring(s: String) -> i32 {
        let mut set = HashSet::new();
        let mut deque = VecDeque::new();
        let mut answer = 0;
        for (i, char) in s.chars().enumerate() {
            // Char has already been seen in the substring, drop chars at the front from vec until it was found
            if set.contains(&char) {
                while let Some(item) = deque.pop_front() {
                    set.remove(&item);
                    if item == char {
                        break;
                    }
                }
            }

            // Add char to set and deque at the end
            set.insert(char);
            deque.push_back(char);
            // The answer is when the deque or set was the largest
            if deque.len() > answer {
                answer = deque.len();
            }
        }
        answer as i32
    }
}

fn run_01() {
    let solution = Solution::length_of_longest_substring(String::from("abcabcbb"));
    assert_eq!(solution, 3);
}

fn run_02() {
    let solution = Solution::length_of_longest_substring(String::from("bbbbb"));
    assert_eq!(solution, 1);
}

fn run_03() {
    let solution = Solution::length_of_longest_substring(String::from("pwwkew"));
    assert_eq!(solution, 3);
}

fn run_04() {
    let solution = Solution::length_of_longest_substring(String::from("tmmzuxt"));
    assert_eq!(solution, 5);
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
}
