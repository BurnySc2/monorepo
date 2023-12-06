use std::collections::{HashMap, VecDeque};

#[derive(PartialEq, Eq, Clone, Debug)]
struct StreamChecker {
    words: Vec<String>,
    keep_track: VecDeque<char>,
    words_ending_with_char: HashMap<char, Vec<String>>,
    longest_word: usize,
}

impl StreamChecker {
    fn new(words: Vec<String>) -> Self {
        let mut longest = 0;
        let mut words_ending_with_char = HashMap::new();
        for word in &words {
            longest = longest.max(word.len());
            let last_char = word.chars().last().unwrap();
            words_ending_with_char
                .entry(last_char)
                .or_insert(Vec::new())
                .push(word.clone());
        }
        StreamChecker {
            words,
            keep_track: VecDeque::new(),
            words_ending_with_char,
            longest_word: longest,
        }
    }

    fn query(&mut self, letter: char) -> bool {
        self.keep_track.push_front(letter);
        if self.keep_track.len() > self.longest_word {
            self.keep_track.pop_back();
        }
        if self.words_ending_with_char.contains_key(&letter) {
            for word in self.words_ending_with_char.get(&letter).unwrap() {
                if self.keep_track.len() < word.len() {
                    continue;
                }

                let mut valid_word = true;
                for (i, j) in self.keep_track.iter().zip(word.chars().rev()) {
                    if i != &j {
                        valid_word = false;
                        break;
                    }
                }
                if valid_word {
                    return valid_word;
                }
            }
        }
        false
    }
}

/**
 * Your StreamChecker object will be instantiated and called as such:
 * let obj = StreamChecker::new(words);
 * let ret_1: bool = obj.query(letter);

[[["ab","ba","aaab","abab","baa"]],["a"],["a"],["a"],["a"],["a"],["b"],["a"],["b"],["a"],["b"],["b"],["b"],["a"],["b"],["a"],["b"],["b"],["b"],["b"],["a"],["b"],["a"],["b"],["a"],["a"],["a"],["b"],["a"],["a"],["a"]]

[null,false,false,false,false,false,true,true,true,true,true,false,false,true,true,true,true,false,false,false,true,true,true,true,true,false,false,true,true,false,false]

[null,false,false,false,false,false,true,true,true,true,true,false,false,true,true,true,true,false,false,false,true,true,true,true,true,true,false,true,true,true,false]

 */

fn run_01() {
    let mut s = StreamChecker::new(vec!["abc".to_string(), "def".to_string()]);
    assert_eq!(s.query('a'), false);
    assert_eq!(s.query('b'), false);
    assert_eq!(s.query('c'), true);
    assert_eq!(s.query('c'), false);
    assert_eq!(s.query('d'), false);
    assert_eq!(s.query('e'), false);
    assert_eq!(s.query('f'), true);
    assert_eq!(s.query('f'), false);
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
