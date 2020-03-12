import unittest

from hypothesis import given
from hypothesis.strategies import integers

from electionguard.dlog import discrete_log
from electionguard.group import ElementModP, ElementModQ, ONE_MOD_P, mult_mod_p, G_INV, g_pow_q


# simpler implementation of discrete_log, only meant for comparison testing of the caching version
def _discrete_log_uncached(e: ElementModP) -> int:
    count = 0
    ginv = ElementModP(G_INV)
    while e != ONE_MOD_P:
        e = mult_mod_p(e, ginv)
        count = count + 1

    return count


class TestDLog(unittest.TestCase):
    @given(integers(0, 100))
    def test_uncached(self, exp: int):
        plaintext = ElementModQ(exp)
        exp_plaintext = g_pow_q(plaintext)
        plaintext_again = _discrete_log_uncached(exp_plaintext)

        self.assertEqual(exp, plaintext_again)

    @given(integers(0, 1000))
    def test_cached(self, exp: int):
        plaintext = ElementModQ(exp)
        exp_plaintext = g_pow_q(plaintext)
        plaintext_again = discrete_log(exp_plaintext)

        self.assertEqual(exp, plaintext_again)

    def test_cached_one(self):
        plaintext = ElementModQ(1)
        ciphertext = g_pow_q(plaintext)
        plaintext_again = discrete_log(ciphertext)

        self.assertEqual(1, plaintext_again)


if __name__ == "__main__":
    unittest.main()
