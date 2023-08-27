#![allow(dead_code)]
#![allow(unused_variables)]
#![feature(test)]
extern crate test;

pub mod problems;

use problems::p416::run_02;

// To generate assembly code:
// cargo rustc -- --emit asm
// Optimized:
// cargo rustc --release -- --emit asm

// Test:
// cargo test
// Bench:
// cargo bench

fn main() {
    println!("Hi, you are running 'cargo run' but should use 'cargo bench' to see the performance of the solutions.");
    // run_01();
    run_02();
}

#[cfg(test)]
mod tests {
    use super::*;
    #[allow(unused_imports)]
    use test::Bencher;
}
