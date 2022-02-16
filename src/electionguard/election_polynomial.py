from dataclasses import dataclass
from typing import Dict, List

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
from .type import GuardianId

SecretCoefficient = ElementModQ  # Secret coefficient of election polynomial
PublicCommitment = ElementModP  # Public commitment of election polynomial


@dataclass
class Coefficient:
    """
    A coefficient of an Election Polynomial
    """

    value: SecretCoefficient
    """The secret coefficient `a_ij` """

    commitment: PublicCommitment
    """The public key `K_ij` generated from secret coefficient"""

    proof: SchnorrProof
    """A proof of possession of the private key for the secret coefficient"""


@dataclass
class ElectionPolynomial:
    """
    A polynomial defined by coefficients

    The 0-index coefficient is used for a secret key which can
    be discovered by a quorum of n guardians corresponding to n coefficients.
    """

    coefficients: List[Coefficient]
    """List of coefficient value, commitments and proofs"""

    def get_commitments(self) -> List[PublicCommitment]:
        """Access the list of public keys generated from secret coefficient"""
        return [coefficient.commitment for coefficient in self.coefficients]

    def get_proofs(self) -> List[SchnorrProof]:
        """Access the list of proof of possesion of the private key for the secret coefficient"""
        return [coefficient.proof for coefficient in self.coefficients]


def generate_polynomial(
    number_of_coefficients: int, nonce: ElementModQ = None
) -> ElectionPolynomial:
    """
    Generates a polynomial for sharing election keys

    :param number_of_coefficients: Number of coefficients of polynomial
    :param nonce: an optional nonce parameter that may be provided (useful for testing)
    :return: Polynomial used to share election keys
    """
    coefficients: List[Coefficient] = []

    for i in range(number_of_coefficients):
        # Note: the nonce value is not safe. it is designed for testing only.
        # this method should be called without the nonce in production.
        value = add_q(nonce, i) if nonce is not None else rand_q()
        commitment = g_pow_p(value)
        proof = make_schnorr_proof(
            ElGamalKeyPair(value, commitment), rand_q()
        )  # TODO Alternate schnoor proof method that doesn't need KeyPair
        coefficient = Coefficient(value, commitment, proof)
        coefficients.append(coefficient)
    return ElectionPolynomial(coefficients)


def compute_polynomial_coordinate(
    exponent_modifier: int, polynomial: ElectionPolynomial
) -> ElementModQ:
    """
    Computes a single coordinate value of the election polynomial used for sharing

    :param exponent_modifier: Unique modifier (usually sequence order) for exponent
    :param polynomial: Election polynomial
    :return: Polynomial used to share election keys
    """

    exponent_modifier_mod_q = ElementModQ(exponent_modifier)

    computed_value = ZERO_MOD_Q
    for (i, coefficient) in enumerate(polynomial.coefficients):
        exponent = pow_q(exponent_modifier_mod_q, i)
        factor = mult_q(coefficient.value, exponent)
        computed_value = add_q(computed_value, factor)
    return computed_value


@dataclass
class LagrangeCoefficientsRecord:
    """
    Record for lagrange coefficients for specific coordinates, usually the guardian sequence order
    to be used in the public election record.
    """

    coefficients: Dict[GuardianId, ElementModQ]


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
    commitments: List[PublicCommitment],
) -> bool:
    """
    Verify a polynomial coordinate value is in fact on the polynomial's curve

    :param coordinate: Value to be checked
    :param exponent_modifier: Unique modifier (usually sequence order) for exponent
    :param commitments: Public commitments for coefficients of polynomial
    :return: True if verified on polynomial
    """

    exponent_modifier_mod_q = ElementModQ(exponent_modifier)

    commitment_output = ONE_MOD_P
    for (i, commitment) in enumerate(commitments):
        exponent = pow_p(exponent_modifier_mod_q, i)
        factor = pow_p(commitment, exponent)
        commitment_output = mult_p(commitment_output, factor)

    value_output = g_pow_p(coordinate)
    return value_output == commitment_output
