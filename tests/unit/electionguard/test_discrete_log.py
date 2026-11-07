import asyncio

from tests.base_test_case import BaseTestCase

from electionguard.constants import get_small_prime
from electionguard.discrete_log import (
    DiscreteLog,
    DiscreteLogExponentError,
    DiscreteLogNotFoundError,
    compute_discrete_log,
)
from electionguard.elgamal import elgamal_encrypt, elgamal_keypair_from_secret
from electionguard.group import (
    ElementModP,
    ONE_MOD_P,
    ONE_MOD_Q,
    TWO_MOD_Q,
    g_pow_p,
    pow_p,
)
from electionguard.utils import get_optional

# far beyond any value the rest of the suite decrypts, so it is never cached
UNCACHED_PLAINTEXT = 2_000_000


class TestDiscreteLog(BaseTestCase):
    """Discrete log singleton tests"""

    def test_settings_apply_to_library_decryption(self):
        # Arrange
        dlog = DiscreteLog.get_instance()
        dlog.set_lazy_evaluation(False)
        self.addCleanup(dlog.set_lazy_evaluation, True)
        keypair = get_optional(elgamal_keypair_from_secret(TWO_MOD_Q))
        ciphertext = get_optional(
            elgamal_encrypt(UNCACHED_PLAINTEXT, ONE_MOD_Q, keypair.public_key)
        )

        # Act & Assert
        with self.assertRaises(DiscreteLogNotFoundError):
            ciphertext.decrypt(keypair.secret_key)

    def test_precompute_cache_async_fills_instance_cache(self):
        # Arrange
        dlog = DiscreteLog.get_instance()
        exponent = max(dlog.get_cache().values()) + 10

        # Act
        asyncio.run(dlog.precompute_cache_async(exponent))

        # Assert
        self.assertEqual(max(dlog.get_cache().values()), exponent)

    def test_max_exponent_is_still_reachable(self):
        # Arrange
        cache = {ONE_MOD_P: 0}

        # Act
        exponent, _ = compute_discrete_log(g_pow_p(1000), cache, max_exponent=1000)

        # Assert
        self.assertEqual(exponent, 1000)
        self.assertEqual(len(cache), 1001)

    def test_exponent_over_the_limit_fails_without_filling_cache(self):
        # Arrange
        cache = {ONE_MOD_P: 0}

        # Act & Assert
        with self.assertRaises(DiscreteLogExponentError):
            compute_discrete_log(g_pow_p(1001), cache, max_exponent=1000)
        self.assertEqual(cache, {ONE_MOD_P: 0})

    def test_value_outside_the_subgroup_fails_without_filling_cache(self):
        # Arrange
        outside_subgroup = next(
            candidate
            for candidate in map(ElementModP, range(2, 100))
            if pow_p(candidate, get_small_prime()) != ONE_MOD_P
        )
        cache = {ONE_MOD_P: 0}

        # Act & Assert
        with self.assertRaisesRegex(DiscreteLogExponentError, "wrong key"):
            compute_discrete_log(outside_subgroup, cache, max_exponent=1000)
        self.assertEqual(cache, {ONE_MOD_P: 0})
