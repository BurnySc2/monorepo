pub struct Solution {}

use std::i32;

impl Solution {
    pub fn find_indices(my_list: &Vec<i32>) -> (Vec<usize>, Vec<usize>) {
        let mut lowest = i32::MAX;
        let mut lowest_index: Option<usize> = None;
        let mut largest = i32::MIN;
        let mut largest_index: Option<usize> = None;
        let mut mins = vec![];
        let mut maxs = vec![];
        for (i, value) in my_list.iter().enumerate() {
            if *value < lowest {
                lowest_index = Some(i);
                lowest = *value;
            // (lowest_index, lowest) = (*i, *value);
            } else if *value > lowest {
                if lowest_index.is_some() {
                    mins.push(lowest_index.unwrap());
                    lowest_index = None;
                }
                lowest = *value;
            }

            // If mins has at least one item
            if !mins.is_empty() {
                if *value > largest {
                    largest_index = Some(i);
                    largest = *value;
                } else if *value < largest {
                    if largest_index.is_some() {
                        maxs.push(largest_index.unwrap());
                        largest_index = None;
                    }
                    largest = *value;
                }
            }
        }
        if lowest_index.is_some() {
            mins.push(lowest_index.unwrap());
        }
        if largest_index.is_some() {
            maxs.push(largest_index.unwrap());
        }
        (mins, maxs)
    }

    pub fn max_profit(prices: Vec<i32>) -> i32 {
        let (mins, maxs) = Solution::find_indices(&prices);
        let mut largest_profit = 0;
        // Try to find N shape profit
        for (min1_index, min1) in mins.iter().enumerate() {
            let min1_val = prices[*min1];
            for (max1_index, max1) in maxs.iter().enumerate() {
                let max1_val = prices[*max1];
                if max1_val <= min1_val || max1 <= min1 {
                    continue;
                }
                let profit1 = max1_val - min1_val;
                // Try to find '/' shape profit
                largest_profit = largest_profit.max(profit1);
                for min2 in mins.iter().skip(min1_index + 1) {
                    if min2 <= max1 {
                        continue;
                    }
                    let min2_val = prices[*min2];
                    for max2 in maxs.iter().skip(max1_index + 1) {
                        if max2 <= min2 {
                            continue;
                        }
                        let max2_val = prices[*max2];
                        let profit2 = max2_val - min2_val;
                        largest_profit = largest_profit.max(profit1 + profit2);
                    }
                }
            }
        }
        largest_profit
    }
}

fn run_01() {
    let solution = Solution::max_profit(vec![3, 3, 5, 0, 0, 3, 1, 4]);
    assert_eq!(solution, 6);
}

fn run_02() {
    let solution = Solution::max_profit(vec![1, 2, 3, 4, 5]);
    assert_eq!(solution, 4);
}

fn run_03() {
    let solution = Solution::max_profit(vec![7, 6, 4, 3, 1]);
    assert_eq!(solution, 0);
}

fn run_04() {
    let solution = Solution::max_profit(vec![1, 5, 4, 6]);
    assert_eq!(solution, 6);
}

fn run_05() {
    let solution = Solution::max_profit(vec![20, 15, 19, 14, 18, 10, 14, 5, 8, 6, 10, 3]);
    assert_eq!(solution, 9);
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
}
