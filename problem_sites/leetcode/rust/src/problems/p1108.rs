pub struct Solution {}

impl Solution {
    pub fn defang_i_paddr(address: String) -> String {
        return address.replace(".", "[.]");
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[allow(unused_imports)]
    use test::Bencher;
}
