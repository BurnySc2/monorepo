pub struct Solution {}

#[derive(PartialEq, Eq, Clone, Debug)]
pub struct ListNode {
    pub val: i32,
    pub next: Option<Box<ListNode>>,
}

impl ListNode {
    #[inline]
    fn new(val: i32) -> Self {
        ListNode { next: None, val }
    }
}

/// Dont need the stuff above for leetcode

impl ListNode {
    fn convert_from_vec(vec: &Vec<i32>) -> Option<Box<ListNode>> {
        if vec.is_empty() {
            return None;
        }
        let mut node = None;
        for i in vec.iter().rev() {
            let mut tmp = ListNode::new(*i);
            tmp.next = node;
            node = Some(Box::new(tmp));
        }
        node
    }

    fn convert_to_vec(mut node: &Option<Box<ListNode>>) -> Vec<i32> {
        let mut vec = Vec::new();
        while let Some(n) = node {
            vec.push(n.val);
            node = &n.next;
        }
        vec
    }
}

impl Solution {
    pub fn merge_k_lists(lists: Vec<Option<Box<ListNode>>>) -> Option<Box<ListNode>> {
        if lists.is_empty() {
            return None;
        }

        let mut values = Vec::new();
        for i in lists {
            for j in ListNode::convert_to_vec(&i) {
                values.push(j)
            }
        }
        values.sort();
        let node = ListNode::convert_from_vec(&values);
        node
    }
}

fn run_01() {
    let vec = vec![
        ListNode::convert_from_vec(&vec![1, 4, 5]),
        ListNode::convert_from_vec(&vec![1, 3, 4]),
        ListNode::convert_from_vec(&vec![2, 6]),
    ];

    let solution = Solution::merge_k_lists(vec);
    let real_solution = vec![1, 1, 2, 3, 4, 4, 5, 6];
    let solution_as_vec = ListNode::convert_to_vec(&solution);
    assert_eq!(solution_as_vec, real_solution);
}

fn run_02() {
    let vec = vec![];

    let solution = Solution::merge_k_lists(vec);
    let real_solution = vec![];
    let solution_as_vec = ListNode::convert_to_vec(&solution);
    assert_eq!(solution_as_vec, real_solution);
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
}
