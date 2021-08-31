from dataclasses import dataclass
from typing import List

from .elgamal import ElGamalKeyPair
from .group import (
    add_q,
    ElementModP,
    ElementModQ,
    g_pow_p,
    div_q,
    mult_p,
    mult_q,
    ONE_MOD_P,
    pow_p,
    pow_q,
    rand_q,
    ZERO_MOD_Q,
)
from .schnorr import make_schnorr_proof, SchnorrProof

SECRET_COEFFICIENT = ElementModQ  # Secret coefficient of election polynomial
PUBLIC_COMMITMENT = ElementModP  # Public commitment of election polynomial


@dataclass
class ElectionPolynomial:
    """
    A polynomial defined by coefficients

    The 0-index coefficient is used for a secret key which can
    be discovered by a quorum of n guardians corresponding to n coefficients.
    """

    coefficients: List[SECRET_COEFFICIENT]
    """The secret coefficients `a_ij` """

    coefficient_commitments: List[PUBLIC_COMMITMENT]
    """The public keys `K_ij`generated from secret coefficients"""

    coefficient_proofs: List[SchnorrProof]
    """A proof of posession of the private key for each secret coefficient"""


def generate_polynomial(
    number_of_coefficients: int, nonce: ElementModQ = None
) -> ElectionPolynomial:
    """
    Generates a polynomial for sharing election keys

    :param number_of_coefficients: Number of coefficients of polynomial
    :param nonce: an optional nonce parameter that may be provided (useful for testing)
    :return: Polynomial used to share election keys
    """
    coefficients: List[SECRET_COEFFICIENT] = []
    commitments: List[PUBLIC_COMMITMENT] = []
    proofs: List[SchnorrProof] = []

    for i in range(number_of_coefficients):
        # Note: the nonce value is not safe.  it is designed for testing only.
        # this method should be called without the nonce in production.
        coefficient = add_q(nonce, i) if nonce is not None else rand_q()
        commitment = g_pow_p(coefficient)
        proof = make_schnorr_proof(
            ElGamalKeyPair(coefficient, commitment), rand_q()
        )  # TODO Alternate schnoor proof method that doesn't need KeyPair

        coefficients.append(coefficient)
        commitments.append(commitment)
        proofs.append(proof)
    return ElectionPolynomial(coefficients, commitments, proofs)


def compute_polynomial_coordinate(
    exponent_modifier: int, polynomial: ElectionPolynomial
) -> ElementModQ:
    """
    Computes a single coordinate value of the election polynomial used for sharing

    :param exponent_modifier: Unique modifier (usually sequence order) for exponent
    :param polynomial: Election polynomial
    :return: Polynomial used to share election keys
    """

    exponent_modifier = ElementModQ(exponent_modifier)

    computed_value = ZERO_MOD_Q
    for (i, coefficient) in enumerate(polynomial.coefficients):
        exponent = pow_q(exponent_modifier, i)
        factor = mult_q(coefficient, exponent)
        computed_value = add_q(computed_value, factor)
    return computed_value


@dataclass
class LagrangeCoefficientsRecord:
    """
    Record for lagrange coefficients for specific coordinates, usually the guardian sequence order
    to be used in the public election record.
    """

    coefficients: List[ElementModQ]


# pylint: disable=unnecessary-comprehension
def compute_lagrange_coefficient(coordinate: int, *degrees: int) -> ElementModQ:
    """
    Compute the lagrange coefficient for a specific coordinate against N degrees.
    :param coordinate: the coordinate to plot, uisually a Guardian's Sequence Order
    :param degrees: the degrees across which to plot, usually the collection of
                    available Guardians' Sequence Orders
    """

    numerator = mult_q(*[degree for degree in degrees])
    denominator = mult_q(*[(degree - coordinate) for degree in degrees])
    result = div_q((numerator), (denominator))
    return result


def verify_polynomial_coordinate(
    coordinate: ElementModQ,
    exponent_modifier: int,
    commitments: List[PUBLIC_COMMITMENT],
) -> bool:
    """
    Verify a polynomial coordinate value is in fact on the polynomial's curve

    :param coordinate: Value to be checked
    :param exponent_modifier: Unique modifier (usually sequence order) for exponent
    :param commitments: Public commitments for coefficients of polynomial
    :return: True if verified on polynomial
    """

    exponent_modifier = ElementModQ(exponent_modifier)

    commitment_output = ONE_MOD_P
    for (i, commitment) in enumerate(commitments):
        exponent = pow_p(exponent_modifier, i)
        factor = pow_p(commitment, exponent)
        commitment_output = mult_p(commitment_output, factor)

    value_output = g_pow_p(coordinate)
    return value_output == commitment_output
