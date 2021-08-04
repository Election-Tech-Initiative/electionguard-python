from tests.base_test_case import BaseTestCase

from electionguard.election_polynomial import (
    compute_polynomial_coordinate,
    ElectionPolynomial,
    generate_polynomial,
    verify_polynomial_coordinate,
)

from electionguard.group import ONE_MOD_P, ONE_MOD_Q, TWO_MOD_P, TWO_MOD_Q

TEST_EXPONENT_MODIFIER = 1
TEST_POLYNOMIAL_DEGREE = 3


class TestElectionPolynomial(BaseTestCase):
    """Election polynomial tests"""

    def test_generate_polynomial(self):
        # Act
        polynomial = generate_polynomial(TEST_POLYNOMIAL_DEGREE)

        # Assert
        self.assertIsNotNone(polynomial)

    def test_compute_polynomial_coordinate(self):
        # Arrange
        polynomial = ElectionPolynomial(
            [ONE_MOD_Q, TWO_MOD_Q],
            [ONE_MOD_P, TWO_MOD_P],
            [],
        )

        # Act
        value = compute_polynomial_coordinate(TEST_EXPONENT_MODIFIER, polynomial)

        # Assert
        self.assertIsNotNone(value)

    def test_verify_polynomial_coordinate(self):
        # Arrange
        polynomial = generate_polynomial(TEST_POLYNOMIAL_DEGREE)

        # Act
        value = compute_polynomial_coordinate(TEST_EXPONENT_MODIFIER, polynomial)

        # Assert
        self.assertTrue(
            verify_polynomial_coordinate(
                value, TEST_EXPONENT_MODIFIER, polynomial.coefficient_commitments
            )
        )
