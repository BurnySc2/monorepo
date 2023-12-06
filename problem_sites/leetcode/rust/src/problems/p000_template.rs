pub struct Solution {}

type Link = Option<Box<ListNode>>;

#[derive(PartialEq, Eq, Clone, Debug)]
pub struct ListNode {
    pub val: i32,
    pub next: Link,
}

impl ListNode {
    #[inline]
    fn new(val: i32) -> Self {
        ListNode {
            next: None,
            val: val,
        }
    }
}

/// Dont need the stuff above for leetcode

impl ListNode {
    fn convert_from_vec(vec: &Vec<i32>) -> Link {
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

    fn convert_to_vec(mut node: &Link) -> Vec<i32> {
        let mut vec = Vec::new();
        while let Some(n) = node {
            vec.push(n.val);
            node = &n.next;
        }
        vec
    }
}

impl Solution {
    pub fn merge_k_lists(lists: Vec<Link>) -> Link {
        Some(Box::new(ListNode::new(0)))
    }
}

fn run_01() {
    let v = vec![1, 2, 3];
    let n = ListNode::convert_from_vec(&v);
    assert!(n.is_some());
    println!("n: {:?}", n);
    let v2 = ListNode::convert_to_vec(&n);
    assert_eq!(v, v2);
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
