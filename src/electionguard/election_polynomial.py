from typing import List, NamedTuple
from math import prod

from .elgamal import ElGamalKeyPair
from .group import (
    add_q,
    ElementModP,
    ElementModQ,
    g_pow_p,
    int_to_p_unchecked,
    int_to_q_unchecked,
    div_q,
    mult_p,
    mult_q,
    ONE_MOD_P,
    ONE_MOD_Q,
    pow_p,
    pow_q,
    rand_q,
    ZERO_MOD_Q,
)
from .schnorr import make_schnorr_proof, SchnorrProof

# TODO: rename to just polynomial and improve the documentation with some links to wikipedia

# TODO: do not use lists here as they are susceptible to order-based attacks
class ElectionPolynomial(NamedTuple):
    """
    ElectionPolynomial is a polynomial defined by coefficients. 
    The 0-index coefficient is used for a secret key which can 
    be discovered by a quorum of n guardians corresponding to n coefficients.
    """

    coefficients: List[ElementModQ]
    """
    The secret coefficients `a_ij`
    """

    coefficient_commitments: List[ElementModP]
    """
    The public keys `K_ij`generated from secret coefficients
    """

    coefficient_proofs: List[SchnorrProof]
    """
    A proof of posession of the private key for each secret coefficient
    """


# TODO: would this be better if we instead took in the list of sequence orders
# along with an optional seed and allowed these to be deterministically created?
def generate_polynomial(
    number_of_coefficients: int, nonce: ElementModQ = None
) -> ElectionPolynomial:
    """
    Generates a polynomial for sharing election keys

    :param number_of_coefficients: Number of coefficients of polynomial
    :return: Polynomial used to share election keys
    """
    coefficients: List[ElementModQ] = []
    commitments: List[ElementModP] = []
    proofs: List[SchnorrProof] = []

    for i in range(number_of_coefficients):
        coefficient = (
            int_to_q_unchecked(nonce.to_int() + i) if nonce is not None else rand_q()
        )
        commitment = g_pow_p(coefficient)
        proof = make_schnorr_proof(
            ElGamalKeyPair(coefficient, commitment), rand_q()
        )  # TODO Alternate schnoor proof method that doesn't need KeyPair

        coefficients.append(coefficient)
        commitments.append(commitment)
        proofs.append(proof)
    return ElectionPolynomial(coefficients, commitments, proofs)


# TODO: compute polynomial coordinate
def compute_polynomial_value(
    exponent_modifier: int, polynomial: ElectionPolynomial
) -> ElementModQ:
    """
    Computes a single coordinate value of the election polynomial used for sharing

    :param exponent_modifier: Unique modifier (usually sequence order) for exponent
    :param polynomial: Election polynomial
    :return: Polynomial used to share election keys
    """
    computed_value = ZERO_MOD_Q
    for (i, coefficient) in enumerate(polynomial.coefficients):
        exponent = pow_q(int_to_q_unchecked(exponent_modifier), int_to_p_unchecked(i))
        factor = mult_q(coefficient, exponent)
        computed_value = add_q(computed_value, factor)
    return computed_value


def compute_lagrange_coefficient(coordinate: int, *degrees: int) -> ElementModQ:
    """
    """

    print(f"coordinate: {coordinate}")
    print(f"degrees: {degrees}")

    numerator = mult_q(*[int_to_q_unchecked(degree) for degree in degrees])
    print(f"numerator: {numerator}")
    denominator = mult_q(
        *[int_to_q_unchecked(degree - coordinate) for degree in degrees]
    )
    print(f"denominator: {denominator}")

    result = div_q((numerator), (denominator))
    print(f"w: {result}")
    return result


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

    # j is my index
    # l is another index
    commitment_output = ONE_MOD_P
    for (i, commitment) in enumerate(coefficient_commitments):
        exponent = pow_p(int_to_p_unchecked(exponent_modifier), int_to_p_unchecked(i))
        factor = pow_p(commitment, exponent)
        commitment_output = mult_p(commitment_output, factor)

    value_output = g_pow_p(value)
    return value_output == commitment_output
