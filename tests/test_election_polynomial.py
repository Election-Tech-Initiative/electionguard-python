from unittest import TestCase

from electionguard.election_polynomial import (
    compute_polynomial_value,
    ElectionPolynomial,
    generate_polynomial,
    verify_polynomial_value,
)

from electionguard.group import ONE_MOD_P, ONE_MOD_Q, TWO_MOD_P, TWO_MOD_Q

TEST_EXPONENT_MODIFIER = 1
TEST_POLYNOMIAL_DEGREE = 3


class TestElectionPolynomial(TestCase):
    def test_generate_polynomial(self):
        polynomial = generate_polynomial(TEST_POLYNOMIAL_DEGREE)
        self.assertIsNotNone(polynomial)

    def test_compute_polynomial_value(self):
        polynomial = ElectionPolynomial(
            [ONE_MOD_Q, TWO_MOD_Q], [ONE_MOD_P, TWO_MOD_P], [],
        )

        value = compute_polynomial_value(TEST_EXPONENT_MODIFIER, polynomial)
        self.assertIsNotNone(value)

    def test_verify_polynomial_value(self):
        polynomial = generate_polynomial(TEST_POLYNOMIAL_DEGREE)
        value = compute_polynomial_value(TEST_EXPONENT_MODIFIER, polynomial)

        self.assertTrue(
            verify_polynomial_value(
                value, TEST_EXPONENT_MODIFIER, polynomial.coefficient_commitments
            )
        )
