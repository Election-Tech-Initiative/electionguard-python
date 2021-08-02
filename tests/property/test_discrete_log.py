import unittest

from hypothesis import given
from hypothesis.strategies import integers

from electionguard.discrete_log import (
    discrete_log,
    discrete_log_async,
    DiscreteLog,
)
from electionguard.group import (
    ElementModP,
    ONE_MOD_P,
    mult_p,
    G,
    g_pow_p,
    int_to_q,
    int_to_p_unchecked,
    int_to_q_unchecked,
    P,
)
from electionguard.utils import get_optional


# simpler implementation of discrete_log, only meant for comparison testing of the caching version
def _discrete_log_uncached(e: ElementModP) -> int:
    count = 0
    g_inv = int_to_p_unchecked(pow(G, -1, P))
    while e != ONE_MOD_P:
        e = mult_p(e, g_inv)
        count = count + 1

    return count


class TestDiscreteLogFunctions(unittest.TestCase):
    """Discrete log tests"""

    @given(integers(0, 100))
    def test_uncached(self, exp: int):
        plaintext = get_optional(int_to_q(exp))
        exp_plaintext = g_pow_p(plaintext)
        plaintext_again = _discrete_log_uncached(exp_plaintext)

        self.assertEqual(exp, plaintext_again)

    @given(integers(0, 1000))
    def test_cached(self, exp: int):
        cache = {ONE_MOD_P: 0}
        plaintext = get_optional(int_to_q(exp))
        exp_plaintext = g_pow_p(plaintext)
        (plaintext_again, returned_cache) = discrete_log(exp_plaintext, cache)

        self.assertEqual(exp, plaintext_again)
        self.assertEqual(len(cache), len(returned_cache))

    def test_cached_one(self):
        cache = {ONE_MOD_P: 0}
        plaintext = int_to_q_unchecked(1)
        ciphertext = g_pow_p(plaintext)
        (plaintext_again, returned_cache) = discrete_log(ciphertext, cache)

        self.assertEqual(1, plaintext_again)
        self.assertEqual(len(cache), len(returned_cache))

    async def test_cached_one_async(self):
        cache = {ONE_MOD_P: 0}
        plaintext = int_to_q_unchecked(1)
        ciphertext = g_pow_p(plaintext)
        (plaintext_again, returned_cache) = await discrete_log_async(ciphertext, cache)

        self.assertEqual(1, plaintext_again)
        self.assertEqual(len(cache), len(returned_cache))


class TestDiscreteLogClass(unittest.TestCase):
    """Discrete log tests"""

    @given(integers(0, 1000))
    def test_cached(self, exp: int):
        plaintext = get_optional(int_to_q(exp))
        exp_plaintext = g_pow_p(plaintext)
        plaintext_again = DiscreteLog().discrete_log(exp_plaintext)

        self.assertEqual(exp, plaintext_again)

    def test_cached_one(self):
        plaintext = int_to_q_unchecked(1)
        ciphertext = g_pow_p(plaintext)
        plaintext_again = DiscreteLog().discrete_log(ciphertext)

        self.assertEqual(1, plaintext_again)

    async def test_cached_one_async(self):
        plaintext = int_to_q_unchecked(1)
        ciphertext = g_pow_p(plaintext)
        plaintext_again = await DiscreteLog().discrete_log_async(ciphertext)

        self.assertEqual(1, plaintext_again)
