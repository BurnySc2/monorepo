class Solution:
    def reverseBits(self, n: int) -> int:  # noqa: N802
        n_reversed = 0
        for i in range(32):
            n_reversed = n_reversed << 1 | n & 1
            if n <= 1:
                n_reversed <<= 32 - i - 1
                return n_reversed
            n >>= 1
        return n_reversed


if __name__ == "__main__":
    from loguru import logger

    s = Solution()

    in1 = 43261596
    expected_out1 = 964176192
    real_out1 = s.reverseBits(in1)
    assert expected_out1 == real_out1, (expected_out1, real_out1, bin(real_out1))

    in2 = 4294967293
    expected_out2 = 3221225471
    real_out2 = s.reverseBits(in2)
    assert expected_out2 == real_out2, (expected_out2, real_out2, bin(real_out2))

    logger.info("done")
