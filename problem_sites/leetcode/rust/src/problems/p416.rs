pub struct Solution {}

impl Solution {
    pub fn can_partition(nums: Vec<i32>) -> bool {
        let nums_sum: i32 = nums.iter().sum();
        if nums_sum % 2 == 1 {
            return false;
        }

        let target = nums_sum / 2;

        let mut my_lookup = Vec::with_capacity(target as usize + 1);
        my_lookup.push(0);
        for _ in 1..=target {
            my_lookup.push(-1)
        }

        for num in nums.iter() {
            for i in (0..=target).rev() {
                if my_lookup[i as usize] > -1 {
                    let new_index = *num + i;
                    if new_index > target {
                        continue;
                    }
                    if new_index < 0 {
                        break;
                    }
                    if my_lookup[new_index as usize] == -1 {
                        my_lookup[new_index as usize] = *num;
                        if new_index == target {
                            return true;
                        }
                    }
                }
            }
        }
        return false;
    }
}

pub fn run_01() {
    let v = vec![1, 2, 3];
    let r = Solution::can_partition(v);
    assert_eq!(r, true);
}

pub fn run_02() {
    let v = vec![3, 3, 3, 4, 5];
    let r = Solution::can_partition(v);
    assert_eq!(r, true);
}
//
// fn run_02() {
//     let v = [[3, 4], [2, 3], [1, 2]]
//         .iter()
//         .map(|x| x.to_vec())
//         .collect::<Vec<_>>();
//     let r = Solution::find_right_interval(v);
//     assert_eq!(r, [-1, 0, 1]);
// }
//
// fn run_03() {
//     let v = [[1, 4], [2, 3], [3, 4]]
//         .iter()
//         .map(|x| x.to_vec())
//         .collect::<Vec<_>>();
//     let r = Solution::find_right_interval(v);
//     assert_eq!(r, [-1, 2, -1]);
// }
//
// fn run_04() {
//     let v = [[1, 2], [2, 3], [2, 3], [3, 4]]
//         .iter()
//         .map(|x| x.to_vec())
//         .collect::<Vec<_>>();
//     let r = Solution::find_right_interval(v);
//     assert_eq!(r, [1, 3, 3, -1]);
// }
//
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

    // #[bench]
    // fn bench_run_03(b: &mut Bencher) {
    //     b.iter(|| run_03());
    // }
    //
    // #[bench]
    // fn bench_run_04(b: &mut Bencher) {
    //     b.iter(|| run_04());
    // }
}
