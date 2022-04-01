import asyncio
from hypothesis import given
from hypothesis.strategies import integers

from tests.base_test_case import BaseTestCase

from electionguard.constants import get_generator, get_large_prime
from electionguard.discrete_log import (
    compute_discrete_log,
    compute_discrete_log_async,
    DiscreteLog,
    precompute_discrete_log_cache,
)
from electionguard.group import (
    ElementModP,
    ElementModQ,
    ONE_MOD_P,
    ONE_MOD_Q,
    mult_p,
    g_pow_p,
)


def _discrete_log_uncached(e: ElementModP) -> int:
    """
    A simpler implementation of discrete_log, only meant for comparison testing of the caching version.
    """
    count = 0
    g_inv = ElementModP(pow(get_generator(), -1, get_large_prime()), False)
    while e != ONE_MOD_P:
        e = mult_p(e, g_inv)
        count = count + 1

    return count


class TestDiscreteLogFunctions(BaseTestCase):
    """Discrete log tests"""

    @given(integers(0, 100))
    def test_uncached(self, exp: int) -> None:
        # Arrange
        plaintext = ElementModQ(exp)
        exp_plaintext = g_pow_p(plaintext)

        # Act
        plaintext_again = _discrete_log_uncached(exp_plaintext)

        # Assert
        self.assertEqual(plaintext, plaintext_again)

    @given(integers(0, 1000))
    def test_cached(self, exp: int) -> None:
        # Arrange
        cache = {ONE_MOD_P: 0}
        plaintext = ElementModQ(exp)
        exp_plaintext = g_pow_p(plaintext)

        # Act
        (plaintext_again, returned_cache) = compute_discrete_log(exp_plaintext, cache)

        # Assert
        self.assertEqual(plaintext, plaintext_again)
        self.assertEqual(len(cache), len(returned_cache))

    def test_cached_one(self) -> None:
        cache = {ONE_MOD_P: 0}
        plaintext = ONE_MOD_Q
        ciphertext = g_pow_p(plaintext)
        (plaintext_again, returned_cache) = compute_discrete_log(ciphertext, cache)

        self.assertEqual(plaintext, plaintext_again)
        self.assertEqual(len(cache), len(returned_cache))

    def test_cached_one_async(self) -> None:
        # Arrange
        cache = {ONE_MOD_P: 0}
        plaintext = ONE_MOD_Q
        ciphertext = g_pow_p(plaintext)

        # Act
        loop = asyncio.new_event_loop()
        (plaintext_again, returned_cache) = loop.run_until_complete(
            compute_discrete_log_async(ciphertext, cache)
        )
        loop.close()

        # Assert
        self.assertEqual(plaintext, plaintext_again)
        self.assertEqual(len(cache), len(returned_cache))

    @given(integers(0, 1000))
    def test_precompute_discrete_log(self, exponent: int) -> None:
        # Arrange
        minimum_cache_size = exponent + 1
        element = g_pow_p(exponent)

        # Act
        cache = precompute_discrete_log_cache(exponent)
        (calculated_exponent, _returned_cache) = compute_discrete_log(element, cache)

        # Assert
        self.assertGreaterEqual(len(cache), minimum_cache_size)
        self.assertEqual(exponent, calculated_exponent)


class TestDiscreteLogClass(BaseTestCase):
    """Discrete log tests"""

    @given(integers(0, 1000))
    def test_precompute(self, exponent: int) -> None:
        # Arrange
        # Due to Singleton it could be bigger on previous run.
        minimum_cache_size = exponent + 1
        element = g_pow_p(exponent)

        # Act
        DiscreteLog().set_lazy_evaluation(False)
        DiscreteLog().precompute_cache(exponent)
        calculated_exponent = DiscreteLog().discrete_log(element)

        # Assert
        self.assertGreaterEqual(len(DiscreteLog().get_cache()), minimum_cache_size)
        self.assertEqual(exponent, calculated_exponent)

    @given(integers(0, 1000))
    def test_cached(self, exp: int) -> None:
        # Arrange
        plaintext = ElementModQ(exp)
        exp_plaintext = g_pow_p(plaintext)

        # Act
        plaintext_again = DiscreteLog().discrete_log(exp_plaintext)

        # Assert
        self.assertEqual(plaintext, plaintext_again)

    def test_cached_one(self) -> None:
        # Arrange
        plaintext = ONE_MOD_Q
        ciphertext = g_pow_p(plaintext)

        # Act
        plaintext_again = DiscreteLog().discrete_log(ciphertext)

        # Assert
        self.assertEqual(plaintext, plaintext_again)

    def test_cached_one_async(self) -> None:
        # Arrange
        plaintext = ONE_MOD_Q
        ciphertext = g_pow_p(plaintext)

        # Act
        loop = asyncio.new_event_loop()
        plaintext_again = loop.run_until_complete(
            DiscreteLog().discrete_log_async(ciphertext)
        )
        loop.close()

        # Assert
        self.assertEqual(plaintext, plaintext_again)
