pub struct Solution {}

use std::collections::HashMap;

impl Solution {
    pub fn find_right_interval(intervals: Vec<Vec<i32>>) -> Vec<i32> {
        if intervals.len() == 0 {
            return vec![];
        }

        let mut intervals2 = vec![];
        for (i, interval) in intervals.iter().enumerate() {
            intervals2.push(vec![interval[0], interval[1], i as i32]);
        }

        let mut intervals_sorted = intervals2.clone();
        // Sort by interval start value, and then by interval-index
        intervals_sorted.sort_by(|a, b| [a[0], a[2]].cmp(&[b[0], b[2]]));
        // println!("{:?}", intervals_sorted);

        let mut results: HashMap<Vec<i32>, i32> = HashMap::new();
        let mut last_index = 0;
        let mut last_inderval_end = std::i32::MAX;

        for (i, interval1) in intervals_sorted.iter().enumerate() {
            // println!("{}, {}, {}", x, y, z);
            if results.contains_key(&vec![interval1[0], interval1[1]]) {
                continue;
            }
            if interval1[1] < last_inderval_end {
                last_index = 0;
            }
            last_inderval_end = interval1[1];
            let start_index = last_index.max(i + 1);
            let mut j2 = 0;
            for (j, interval2) in intervals_sorted.iter().skip(start_index).enumerate() {
                if interval1[1] <= interval2[0] {
                    // println!("{:?} {:?}", interval1, interval2);
                    results.insert(vec![interval1[0], interval1[1]], interval2[2]);
                    break;
                }
                j2 = j;
            }
            last_index = j2
        }

        let mut return_result = vec![];
        for interval in intervals2 {
            let index = results.get(&vec![interval[0], interval[1]]);
            let val = index.unwrap_or(&-1);
            return_result.push(*val);
        }

        return_result
    }
}

fn run_01() {
    let v = [[1, 2]].iter().map(|x| x.to_vec()).collect::<Vec<_>>();
    let r = Solution::find_right_interval(v);
    assert_eq!(r, [-1]);
}

fn run_02() {
    let v = [[3, 4], [2, 3], [1, 2]]
        .iter()
        .map(|x| x.to_vec())
        .collect::<Vec<_>>();
    let r = Solution::find_right_interval(v);
    assert_eq!(r, [-1, 0, 1]);
}

fn run_03() {
    let v = [[1, 4], [2, 3], [3, 4]]
        .iter()
        .map(|x| x.to_vec())
        .collect::<Vec<_>>();
    let r = Solution::find_right_interval(v);
    assert_eq!(r, [-1, 2, -1]);
}

fn run_04() {
    let v = [[1, 2], [2, 3], [2, 3], [3, 4]]
        .iter()
        .map(|x| x.to_vec())
        .collect::<Vec<_>>();
    let r = Solution::find_right_interval(v);
    assert_eq!(r, [1, 3, 3, -1]);
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
