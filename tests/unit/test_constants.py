from tests.base_test_case import BaseTestCase


from electionguard.constants import (
    PrimeOption,
    LARGE_TEST_CONSTANTS,
    get_constants,
    STANDARD_CONSTANTS,
    using_test_constants,
    push_new_constants,
    pop_constants,
)

from electionguard.constants import (
    get_small_prime,
    get_large_prime,
    get_cofactor,
    get_generator,
)


class TestConstants(BaseTestCase):
    """Election constant tests."""

    def test_get_standard_primes(self):
        """Test getting standard constants with large primes."""
        # Act
        push_new_constants(PrimeOption.Standard)

        try:
            constants = get_constants()

            # Assert
            self.assertIsNotNone(constants)
            self.assertEqual(constants, STANDARD_CONSTANTS)
            self.assertEqual(constants.large_prime, get_large_prime())
            self.assertEqual(constants.small_prime, get_small_prime())
            self.assertEqual(constants.cofactor, get_cofactor())
            self.assertEqual(constants.generator, get_generator())
            self.assertFalse(using_test_constants())
        except BaseException as e:
            pop_constants()  # undo changes to the constants before failing
            raise e

        pop_constants()  # undo changes to the constants before returning

    def test_get_test_primes(self):
        """Test getting test only constants with small primes."""
        # Act
        push_new_constants(PrimeOption.TestOnly)

        try:
            constants = get_constants()

            # Assert
            self.assertIsNotNone(constants)
            self.assertEqual(constants, LARGE_TEST_CONSTANTS)
            self.assertEqual(constants.large_prime, get_large_prime())
            self.assertEqual(constants.small_prime, get_small_prime())
            self.assertEqual(constants.cofactor, get_cofactor())
            self.assertEqual(constants.generator, get_generator())
            self.assertTrue(using_test_constants())
        except BaseException as e:
            pop_constants()  # undo changes to the constants before failing
            raise e

        pop_constants()  # undo changes to the constants before returning
