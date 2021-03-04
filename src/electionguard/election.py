from dataclasses import dataclass

from .group import Q, P, R, G, ElementModQ, ElementModP
from .hash import hash_elems
from .serializable import Serializable


@dataclass(eq=True, unsafe_hash=True)
class ElectionConstants(Serializable):
    """
    The constants for mathematical functions during the election.
    """

    large_prime = P
    """large prime or p"""

    small_prime = Q
    """small prime or q"""

    cofactor = R
    """cofactor or r"""

    generator = G
    """generator or g"""


@dataclass(eq=True, unsafe_hash=True)
class CiphertextElectionContext(Serializable):
    """
    `CiphertextElectionContext` is the ElectionGuard representation of a specific election
    Note: The ElectionGuard Data Spec deviates from the NIST model in that
    this object includes fields that are populated in the course of encrypting an election
    Specifically, `crypto_base_hash`, `crypto_extended_base_hash` and `elgamal_public_key`
    are populated with election-specific information necessary for encrypting the election.
    Refer to the [Electionguard Specification](https://github.com/microsoft/electionguard) for more information.

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

    # the `joint public key (K)` in the [ElectionGuard Spec](https://github.com/microsoft/electionguard/wiki)
    elgamal_public_key: ElementModP

    # the `commitment hash H(K 1,0 , K 2,0 ... , K n,0 )` of the public commitments
    # guardians make to each other in the [ElectionGuard Spec](https://github.com/microsoft/electionguard/wiki)
    commitment_hash: ElementModQ

    # The hash of the election metadata
    description_hash: ElementModQ

    # the `base hash code (𝑄)` in the [ElectionGuard Spec](https://github.com/microsoft/electionguard/wiki)
    crypto_base_hash: ElementModQ

    # the `extended base hash code (𝑄')` in the [ElectionGuard Spec](https://github.com/microsoft/electionguard/wiki)
    crypto_extended_base_hash: ElementModQ


def make_ciphertext_election_context(
    number_of_guardians: int,
    quorum: int,
    elgamal_public_key: ElementModP,
    commitment_hash: ElementModQ,
    description_hash: ElementModQ,
) -> CiphertextElectionContext:
    """
    Makes a CiphertextElectionContext object.

    :param number_of_guardians: The number of guardians necessary to generate the public key
    :param quorum: The quorum of guardians necessary to decrypt an election.  Must be less than `number_of_guardians`
    :param elgamal_public_key: the public key of the election
    :param commitment_hash: the hash of the commitments the guardians make to each other
    :param description_hash: the hash of the election metadata
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
        P, Q, G, number_of_guardians, quorum, description_hash
    )
    crypto_extended_base_hash = hash_elems(crypto_base_hash, commitment_hash)
    return CiphertextElectionContext(
        number_of_guardians=number_of_guardians,
        quorum=quorum,
        elgamal_public_key=elgamal_public_key,
        commitment_hash=commitment_hash,
        description_hash=description_hash,
        crypto_base_hash=crypto_base_hash,
        crypto_extended_base_hash=crypto_extended_base_hash,
    )
