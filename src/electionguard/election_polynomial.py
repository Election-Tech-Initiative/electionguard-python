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
)
from .schnorr import make_schnorr_proof, SchnorrProof


class ElectionPolynomial(NamedTuple):
    coefficients: List[ElementModQ]
    coefficient_commitments: List[ElementModP]
    coefficient_proofs: List[SchnorrProof]


def generate_polynomial(number_of_coefficients: int) -> ElectionPolynomial:
    polynomial = ElectionPolynomial([], [], [])
    for i in range(number_of_coefficients):
        coefficient = rand_q()
        commitment = g_pow_p(coefficient)
        proof = make_schnorr_proof(
            ElGamalKeyPair(coefficient, commitment), rand_q()
        )  # FIXME Alternate schnoor proof method that doesn't need KeyPair

        polynomial.coefficients.append(coefficient)
        polynomial.coefficient_commitments.append(commitment)
        polynomial.coefficient_proofs.append(proof)
    return polynomial


def compute_polynomial_value(
    exponent_modifier: int, polynomial: ElectionPolynomial
) -> ElementModQ:
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
    # FIXME Revisit mod p over mod q
    commitment_output = ONE_MOD_P
    for (i, commitment) in enumerate(coefficient_commitments):
        exponent = pow_p(int_to_p_unchecked(exponent_modifier), int_to_p_unchecked(i))
        factor = pow_p(commitment, exponent)
        commitment_output = mult_p(commitment_output, factor)

    value_output = g_pow_p(value)
    return value_output == commitment_output
