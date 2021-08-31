"""Context for election encryption."""

from dataclasses import dataclass
from typing import Dict, Optional

from .constants import get_small_prime, get_large_prime, get_generator
from .group import (
    ElementModQ,
    ElementModP,
)
from .hash import hash_elems

# pylint: disable=too-many-instance-attributes
@dataclass(eq=True, unsafe_hash=True)
class CiphertextElectionContext:
    """`CiphertextElectionContext` is the ElectionGuard representation of a specific election.

    Note: The ElectionGuard Data Spec deviates from the NIST model in that
    this object includes fields that are populated in the course of encrypting an election
    Specifically, `crypto_base_hash`, `crypto_extended_base_hash` and `elgamal_public_key`
    are populated with election-specific information necessary for encrypting the election.
    Refer to the specification for more information.

    To make an instance of this class, don't construct it directly. Use
    `make_ciphertext_election_context` instead.
    """

    number_of_guardians: int
    """
    The number of guardians necessary to generate the public key
    """
    quorum: int
    """
    The quorum of guardians necessary to decrypt an election.  Must be less than `number_of_guardians`
    """

    elgamal_public_key: ElementModP
    """the `joint public key (K)` in the specification"""

    commitment_hash: ElementModQ
    """
    the `commitment hash H(K 1,0 , K 2,0 ... , K n,0 )` of the public commitments
    guardians make to each other in the specification
    """

    manifest_hash: ElementModQ
    """The hash of the election metadata"""

    crypto_base_hash: ElementModQ
    """The `base hash code (𝑄)` in the specification"""

    crypto_extended_base_hash: ElementModQ
    """The `extended base hash code (𝑄')` in specification"""

    extended_data: Optional[Dict[str, str]]
    """Data to allow extending the context for special cases."""


def make_ciphertext_election_context(
    number_of_guardians: int,
    quorum: int,
    elgamal_public_key: ElementModP,
    commitment_hash: ElementModQ,
    manifest_hash: ElementModQ,
    extended_data: Optional[Dict[str, str]] = None,
) -> CiphertextElectionContext:
    """
    Makes a CiphertextElectionContext object.

    :param number_of_guardians: The number of guardians necessary to generate the public key
    :param quorum: The quorum of guardians necessary to decrypt an election.  Must be less than `number_of_guardians`
    :param elgamal_public_key: the public key of the election
    :param commitment_hash: the hash of the commitments the guardians make to each other
    :param manifest_hash: the hash of the election metadata
    """

    # What's a crypto_base_hash?
    # The metadata of this object are hashed together with the
    # - prime modulus (𝑝),
    # - subgroup order (𝑞),
    # - generator (𝑔),
    # - number of guardians (𝑛),
    # - decryption threshold value (𝑘),
    # to form a base hash code (𝑄) which will be incorporated
    # into every subsequent hash computation in the election.

    # What's a crypto_extended_base_hash?
    # Once the baseline parameters have been produced and confirmed,
    # all of the public guardian commitments 𝐾𝑖,𝑗 are hashed together
    # with the base hash 𝑄 to form an extended base hash 𝑄' that will
    # form the basis of subsequent hash computations.

    crypto_base_hash = hash_elems(
        ElementModP(get_large_prime(), False),
        ElementModQ(get_small_prime(), False),
        ElementModP(get_generator(), False),
        number_of_guardians,
        quorum,
        manifest_hash,
    )
    crypto_extended_base_hash = hash_elems(crypto_base_hash, commitment_hash)
    return CiphertextElectionContext(
        number_of_guardians,
        quorum,
        elgamal_public_key,
        commitment_hash,
        manifest_hash,
        crypto_base_hash,
        crypto_extended_base_hash,
        extended_data,
    )
