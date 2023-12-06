pub struct Solution {}

impl Solution {
    pub fn largest_rectangle_area(heights: Vec<i32>) -> i32 {
        let mut biggest_area = 0;
        let mut previous_value = 0;
        for (index, mut start_height) in heights.iter().enumerate() {
            if start_height == &0i32 {
                continue;
            }
            if *start_height <= previous_value {
                previous_value = *start_height;
                continue;
            }
            let mut area = *start_height;
            for (distance, end_height) in heights.iter().skip(index + 1).enumerate() {
                // println!("Start, end, biggest, area: {} {} {} {}", start_height, end_height, biggest_area, area);
                if end_height < start_height {
                    start_height = end_height;
                }
                area = area.max(start_height * (distance + 2) as i32);
            }
            biggest_area = biggest_area.max(area)
        }
        biggest_area
    }
}

fn run_01() {
    let solution = Solution::largest_rectangle_area(vec![2, 1, 5, 6, 2, 3]);
    assert_eq!(solution, 10);
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
}
