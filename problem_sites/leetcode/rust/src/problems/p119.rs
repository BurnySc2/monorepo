pub struct Solution {}

use std::collections::HashMap;

// Simple ncr using u128

// pub fn factorial(n: u128) -> u128 {
//     let mut number = 1;
//     for i in 2..=n {
//         number *= i;
//     }
//     number
// }
//
// pub fn ncr(n: i32, k: i32) -> i32 {
//     let n128 = n as u128;
//     let k128 = k as u128;
//     (factorial(n128) / (factorial(n128 - k128) * factorial(k128))) as i32
// }

// Limit ncr to i32 but support 33rd row of pascals triangle

pub fn primes(limit: i32) -> Vec<i32> {
    // Can be improved by using sieve instead
    let mut primes = vec![2];
    for i in (3..=limit).step_by(2) {
        let mut is_prime = true;
        for j in &primes {
            if i % j == 0 {
                is_prime = false;
                break;
            }
        }
        if is_prime {
            primes.push(i);
        }
    }
    primes
}

pub fn prime_factorization(primes: &Vec<i32>, n: i32) -> HashMap<i32, i32> {
    let mut map = HashMap::new();
    let mut index = 0;
    let mut mut_n = n;
    loop {
        if index >= primes.len() || mut_n == 1 {
            break;
        }
        let prime = primes[index];
        while mut_n % prime == 0 {
            *map.entry(prime).or_insert(0) += 1;
            mut_n /= prime;
        }
        index += 1;
    }
    if mut_n != 1 {
        map.insert(mut_n, 1);
    }
    map
}

pub fn ncr(n: i32, k: i32) -> i32 {
    if k == n || k == 0 {
        return 1;
    }
    // Get primes
    let primes_list = primes(n);
    // Skip values in loop, e.g. n=30, k=10, only 21 to =30 has to be looped
    let numerator_start_value = k.max(n - k) + 1;
    // Denominator: only have to loop from 2 to =10
    let denominator_end_value = k.min(n - k);
    // Prime factorization factors: 9 = {2: 2, 3: 1} = 2^2 + 3^1
    let mut factors = HashMap::new();

    // Get factors for numerator
    for i in numerator_start_value..=n {
        for (key, val) in prime_factorization(&primes_list, i as i32) {
            *factors.entry(key).or_insert(0) += val;
        }
    }

    // Subtract factors from denominator
    for i in 2..=denominator_end_value {
        for (key, val) in prime_factorization(&primes_list, i as i32) {
            *factors.entry(key).or_insert(0) -= val;
        }
    }

    // Calculate the product from the remaining prime factors
    let mut product = 1;
    for (key, val) in factors {
        assert!(val >= 0);
        if val > 0 {
            product *= key.pow(val as u32);
        }
    }
    product
}

impl Solution {
    pub fn get_row(row_index: i32) -> Vec<i32> {
        let mut result = vec![];
        // Calculate first half oof pascals triangle
        for k in 0..=(row_index / 2) {
            result.push(ncr(row_index, k));
        }
        // Use symmetry of pascals triangle
        let skip_val = if row_index % 2 == 0 { 1 } else { 0 };
        for i in result.clone().iter().rev().skip(skip_val) {
            result.push(*i);
        }
        result
    }
}

fn run_01() {
    let solution = Solution::get_row(3);
    let result = vec![1, 3, 3, 1];
    assert_eq!(solution, result);
}

fn run_02() {
    let solution = Solution::get_row(4);
    let result = vec![1, 4, 6, 4, 1];
    assert_eq!(solution, result);
}

fn run_03() {
    let solution = Solution::get_row(13);
    let result = vec![
        1, 13, 78, 286, 715, 1287, 1716, 1716, 1287, 715, 286, 78, 13, 1,
    ];
    assert_eq!(solution, result);
}

fn run_04() {
    let solution = Solution::get_row(33);
    let result = vec![
        1, 33, 528, 5456, 40920, 237336, 1107568, 4272048, 13884156, 38567100, 92561040, 193536720,
        354817320, 573166440, 818809200, 1037158320, 1166803110, 1166803110, 1037158320, 818809200,
        573166440, 354817320, 193536720, 92561040, 38567100, 13884156, 4272048, 1107568, 237336,
        40920, 5456, 528, 33, 1,
    ];
    assert_eq!(solution, result);
}

fn run_prime_fac_01() {
    let primes = vec![2, 3, 5, 7, 11, 13, 17, 19];
    let solution = prime_factorization(&primes, 10);
    let result: HashMap<i32, i32> = [(2, 1), (5, 1)].iter().cloned().collect();
    assert_eq!(solution, result);
}

fn run_prime_fac_02() {
    let primes = vec![2, 3, 5, 7, 11, 13, 17, 19];
    let solution = prime_factorization(&primes, 12);
    let result: HashMap<i32, i32> = [(2, 2), (3, 1)].iter().cloned().collect();
    assert_eq!(solution, result);
}

fn run_primes_01() {
    let primes_list = vec![2, 3, 5, 7, 11, 13, 17, 19];
    let solution = primes(20);
    assert_eq!(solution, primes_list);
}

fn run_ncr_01() {
    let solution = ncr(33, 3);
    let result = 5456;
    assert_eq!(solution, result);
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
    fn bench_run_prime_fac_01(b: &mut Bencher) {
        b.iter(|| run_prime_fac_01());
    }

    #[bench]
    fn bench_run_prime_fac_02(b: &mut Bencher) {
        b.iter(|| run_prime_fac_02());
    }

    #[bench]
    fn bench_run_primes_01(b: &mut Bencher) {
        b.iter(|| run_primes_01());
    }

    #[bench]
    fn bench_run_ncr_01(b: &mut Bencher) {
        b.iter(|| run_ncr_01());
    }
}
