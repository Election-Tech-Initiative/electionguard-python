"""Context for election encryption."""

from dataclasses import dataclass, field
from typing import Dict, Optional

from .constants import get_small_prime, get_large_prime, get_generator
from .elgamal import ElGamalPublicKey
from .group import (
    ElementModQ,
    ElementModP,
)
from .hash import hash_elems


@dataclass
class Configuration:
    """Configuration of election to allow edge cases."""

    allow_overvotes: bool = field(default=True)
    """
    Allow overvotes, votes exceeding selection limit, for the election.
    """

    max_votes: int = field(default=1_000_000)
    """
    Maximum votes, the maximum votes allowed on a selection for an aggregate ballot or tally.
    This can also be seen as the maximum ballots where a selection on a ballot can only have one vote.
    """


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
    The quorum of guardians necessary to decrypt an election.  Must be fewer than `number_of_guardians`
    """

    elgamal_public_key: ElGamalPublicKey
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

    configuration: Configuration = field(default_factory=Configuration)
    """Configuration for the election edge cases."""

    def get_extended_data_field(self, field_name: str) -> Optional[str]:
        """Returns the value for a field in the extended data or None if it isn't initialized."""

        if self.extended_data is None:
            return None
        return self.extended_data.get(field_name)


def make_ciphertext_election_context(
    number_of_guardians: int,
    quorum: int,
    elgamal_public_key: ElGamalPublicKey,
    commitment_hash: ElementModQ,
    manifest_hash: ElementModQ,
    extended_data: Optional[Dict[str, str]] = None,
) -> CiphertextElectionContext:
    """
    Makes a CiphertextElectionContext object.

    :param number_of_guardians: The number of guardians necessary to generate the public key
    :param quorum: The quorum of guardians necessary to decrypt an election.  Must be fewer than `number_of_guardians`
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
