pub struct Solution {}

/// Example below: candies = inf, num_people = 4
/// 1+2+3+4 = (4+1)*4/2 = 20/2 = 10
/// How many candies are required for a full round?
/// 1 round: candies - (n+1)*n/2 where n = num_people * 1
/// 2 rounds: candies - (n+1)*n/2 where n = num_people * 2
/// 3 rounds: candies - (n+1)*n/2 where n = num_people * 3
///
/// [1, 0, 0, 0]
/// [1, 2, 0, 0]
/// [1, 2, 3, 0]
/// [1, 2, 3, 4]
/// [6, 2, 3, 4]
/// [6, 8, 3, 4]
/// [6, 8, 10, 4]
/// [6, 8, 10, 12]
/// [15, 8, 10, 12]
/// [15, 18, 21, 24]
///
/// first person:
/// [1 + (n + 1) + (n + 1) * 2, ...]
/// [1 + 3 * (n + 1), ...]
/// [3n + 4, ...]
///
/// [1 + (n + 1) + (n + 1) * 2 + (n + 1) * 3, ...]
/// [1 + 3 * (n + 1), ...]
/// [6n + 7, ...]
///
/// second person:
/// [..., 2 + (n+2) + (n+2)*2, ...]
/// [..., 3n + 8, ...]

impl Solution {
    pub fn distribute_candies(candies: i32, num_people: i32) -> Vec<i32> {
        if num_people == 0 {
            return vec![];
        }

        let mut rounds = 0;
        let mut final_round_candies = candies;
        {
            let mut r = 1;
            loop {
                // Total hand outs this round, e.g. 4 for 1 round if num_people=4, 8 for 2 rounds if num_people=4 etc.
                let hand_outs = r * num_people;
                let required_candies = (hand_outs + 1) * hand_outs / 2;
                if required_candies > candies {
                    break;
                }
                rounds = r;
                final_round_candies = candies - required_candies;

                r += 1;
            }
        }
        // println!("Enough for rounds: {}", rounds);
        // println!("Remaining candies: {}", final_round_candies);

        let mut result = vec![];
        let n = (rounds - 1) * rounds / 2;
        for i in 1..=num_people {
            // Calculate the amount of candies for the current person
            let mut previous_rounds_candies = 0;
            if rounds > 0 {
                previous_rounds_candies = num_people * n + i * rounds;
            }
            let mut current_round_candies = rounds * num_people + i;

            // Reduce the amount of candies available for this round
            current_round_candies = current_round_candies.min(final_round_candies);
            final_round_candies -= current_round_candies;

            let total = previous_rounds_candies + current_round_candies;
            // println!("canditate {} got {} candies previous rounds and this round {} totalling {}", i, previous_rounds_candies, current_round_candies, total);
            result.push(total);
        }
        result
    }
}

fn run_01() {
    let solution = Solution::distribute_candies(7, 4);
    let real_solution = vec![1, 2, 3, 1];
    assert_eq!(solution, real_solution);
}

fn run_02() {
    let solution = Solution::distribute_candies(10, 3);
    let real_solution = vec![5, 2, 3];
    assert_eq!(solution, real_solution);
}

fn run_03() {
    let solution = Solution::distribute_candies(21, 3);
    let real_solution = vec![5, 7, 9];
    assert_eq!(solution, real_solution);
}

fn run_04() {
    let solution = Solution::distribute_candies(1, 1);
    let real_solution = vec![1];
    assert_eq!(solution, real_solution);
}

fn run_05() {
    let solution = Solution::distribute_candies(80, 4);
    let real_solution = vec![17, 18, 21, 24];
    assert_eq!(solution, real_solution);
}

fn run_06() {
    let solution = Solution::distribute_candies(100, 0);
    let real_solution = vec![];
    assert_eq!(solution, real_solution);
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
