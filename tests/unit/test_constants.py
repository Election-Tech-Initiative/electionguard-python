import os
from unittest import TestCase
from unittest.mock import patch

from electionguard.constants import (
    PrimeOption,
    get_constants,
    STANDARD_CONSTANTS,
    MEDIUM_TEST_CONSTANTS,
)

from electionguard.constants import (
    get_small_prime,
    get_large_prime,
    get_cofactor,
    get_generator,
)


class TestConstants(TestCase):
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
        self.assertEqual(constants, MEDIUM_TEST_CONSTANTS)
        self.assertEqual(constants.large_prime, get_large_prime())
        self.assertEqual(constants.small_prime, get_small_prime())
        self.assertEqual(constants.cofactor, get_cofactor())
        self.assertEqual(constants.generator, get_generator())
