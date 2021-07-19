import os
from unittest.mock import patch

from tests.base_test_case import BaseTestCase


from electionguard.constants import (
    PrimeOption,
    LARGE_TEST_CONSTANTS,
    get_constants,
    STANDARD_CONSTANTS,
)

from electionguard.constants import (
    get_small_prime,
    get_large_prime,
    get_cofactor,
    get_generator,
)


class TestConstants(BaseTestCase):
    """Election constant tests."""

    @patch.dict(os.environ, {"PRIME_OPTION": PrimeOption.Standard.value})
    def test_get_standard_primes(self):
        """Test getting standard constants with large primes."""
        # Act
        constants = get_constants()

        # Assert
        self.assertIsNotNone(constants)
        self.assertEqual(constants, STANDARD_CONSTANTS)
        self.assertEqual(constants.large_prime, get_large_prime())
        self.assertEqual(constants.small_prime, get_small_prime())
        self.assertEqual(constants.cofactor, get_cofactor())
        self.assertEqual(constants.generator, get_generator())

    @patch.dict(os.environ, {"PRIME_OPTION": PrimeOption.TestOnly.value})
    def test_get_test_primes(self):
        """Test getting test only constants with small primes."""
        # Act
        constants = get_constants()

        # Assert
        self.assertIsNotNone(constants)
        self.assertEqual(constants, LARGE_TEST_CONSTANTS)
        self.assertEqual(constants.large_prime, get_large_prime())
        self.assertEqual(constants.small_prime, get_small_prime())
        self.assertEqual(constants.cofactor, get_cofactor())
        self.assertEqual(constants.generator, get_generator())
