from typing import List, NamedTuple

from .elgamal import ElGamalKeyPair
from .group import (
    add_q,
    ElementModP,
    ElementModQ,
    g_pow_p,
    int_to_p_unchecked,
    int_to_q_unchecked,
    mult_p,
    mult_q,
    ONE_MOD_P,
    pow_p,
    pow_q,
    rand_q,
    ZERO_MOD_Q,
    Q,
)
from .schnorr import make_schnorr_proof, SchnorrProof


class ElectionPolynomial(NamedTuple):
    """
    ElectionPolynomial is a polynomial defined by coefficients. The 0 coefficient is used for a secret key which can 
    be discovered by a quorum of n guardians corresponding to n coefficients.
    """

    coefficients: List[ElementModQ]
    coefficient_commitments: List[ElementModP]
    coefficient_proofs: List[SchnorrProof]


def generate_polynomial(number_of_coefficients: int) -> ElectionPolynomial:
    """
    Generates a polynomial for sharing election keys

    :param number_of_coefficients: Number of coefficients of polynomial
    :return: Polynomial used to share election keys
    """
    coefficients: List[ElementModQ] = []
    commitments: List[ElementModP] = []
    proofs: List[SchnorrProof] = []
    polynomial = ElectionPolynomial(coefficients, commitments, proofs)

    assert number_of_coefficients > 0, "must have a positive number of coefficients"

    # TODO: you might want to have an optional argument -- a nonce -- from which you derive all
    #   the coefficients, rather than making them all be random here. That would make this function
    #   deterministic and thus more testable. Of course, when used "for real", you'd make sure that
    #   the input nonce was truly random.

    for i in range(number_of_coefficients):
        coefficient = rand_q()
        commitment = g_pow_p(coefficient)
        proof = make_schnorr_proof(
            ElGamalKeyPair(coefficient, commitment), rand_q()
        )  # TODO Alternate schnoor proof method that doesn't need KeyPair

        polynomial.coefficients.append(coefficient)
        polynomial.coefficient_commitments.append(commitment)
        polynomial.coefficient_proofs.append(proof)
    return polynomial


def compute_polynomial_value(
    exponent_modifier: int, polynomial: ElectionPolynomial
) -> ElementModQ:
    """
    Computes a single value of the election polynomial used for sharing

    :param exponent_modifier: Unique modifier (usually sequence order) for exponent
    :param polynomial: Election polynomial
    :return: Polynomial used to share election keys
    """

    assert 0 <= exponent_modifier < Q, "exponent_modifier is out of range"

    computed_value = ZERO_MOD_Q
    for (i, coefficient) in enumerate(polynomial.coefficients):
        exponent = pow_q(int_to_q_unchecked(exponent_modifier), int_to_p_unchecked(i))
        factor = mult_q(coefficient, exponent)
        computed_value = add_q(computed_value, factor)
    return computed_value


def verify_polynomial_value(
    value: ElementModQ,
    exponent_modifier: int,
    coefficient_commitments: List[ElementModP],
) -> bool:
    """
    Verify a polynomial value is in fact on the polynomial's curve

    :param value: Value to be checked
    :param exponent_modifier: Unique modifier (usually sequence order) for exponent
    :param coefficient_commitments: Commitments for coefficients of polynomial
    :return: True if verified on polynomial
    """
    commitment_output = ONE_MOD_P
    for (i, commitment) in enumerate(coefficient_commitments):
        exponent = pow_p(int_to_p_unchecked(exponent_modifier), int_to_p_unchecked(i))
        factor = pow_p(commitment, exponent)
        commitment_output = mult_p(commitment_output, factor)

    value_output = g_pow_p(value)
    return value_output == commitment_output
