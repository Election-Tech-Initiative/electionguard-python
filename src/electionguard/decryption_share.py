from dataclasses import dataclass, field, InitVar
from typing import Optional, List, Any, Sequence, Dict

from .chaum_pedersen import ChaumPedersenProof
from .election_object_base import ElectionObjectBase

from .elgamal import ElGamalCiphertext, elgamal_add
from .group import add_q, ElementModP, ElementModQ, ZERO_MOD_Q
from .hash import CryptoHashCheckable, hash_elems
from .logs import log_warning


@dataclass
class CiphertextDecryptionSelection(ElectionObjectBase, CryptoHashCheckable):
    """
    """

    # The SelectionDescription hash
    description_hash: ElementModQ

    # M_i in the spec
    share: ElementModP

    # Proof that the share was decrypted correctly
    proof: ChaumPedersenProof

    def crypto_hash_with(self, seed_hash: ElementModQ) -> ElementModQ:
        """
        Generates a hash with a given seed that can be checked later against the seed and class metadata.
        """
        ...


@dataclass
class CiphertextPartialDecryptionSelection(ElectionObjectBase, CryptoHashCheckable):
    """
    """

    # The SelectionDescription hash
    description_hash: ElementModQ

    # M_i in the spec
    partial_share: ElementModP

    # Proof that the share was decrypted correctly
    proof: ConstantChaumPedersenProof

    def crypto_hash_with(self, seed_hash: ElementModQ) -> ElementModQ:
        """
        Generates a hash with a given seed that can be checked later against the seed and class metadata.
        """
        ...


@dataclass
class CiphertextDecryptionContest(ElectionObjectBase, CryptoHashCheckable):
    """
    """

    # The ContestDescription Hash
    description_hash: ElementModQ

    # the collection of decryption shares for this contest's selections
    selections: Dict[str, CiphertextDecryptionSelection]

    def crypto_hash_with(self, seed_hash: ElementModQ) -> ElementModQ:
        """
        Generates a hash with a given seed that can be checked later against the seed and class metadata.
        """
        ...


@dataclass
class CiphertextPartialDecryptionContest(ElectionObjectBase, CryptoHashCheckable):
    """
    """

    # The ContestDescription Hash
    description_hash: ElementModQ

    # the collection of decryption shares for this contest's selections
    selections: Dict[str, CiphertextPartialDecryptionSelection]

    def crypto_hash_with(self, seed_hash: ElementModQ) -> ElementModQ:
        """
        Generates a hash with a given seed that can be checked later against the seed and class metadata.
        """
        ...


@dataclass
class DecryptionShare:
    """
    """

    # The Available Guardian that this share belongs to
    guardian_id: str

    # The collection of all contests in the election
    contests: Dict[str, CiphertextDecryptionContest]

    def crypto_hash_with(self, seed_hash: ElementModQ) -> ElementModQ:
        """
        Generates a hash with a given seed that can be checked later against the seed and class metadata.
        """
        ...


@dataclass
class PartialDecryptionShare:
    """
    """

    # The Available Guardian that this partial share belongs to
    available_guardian_id: str

    # The Missing Guardian for whom this share is calculated on behalf of
    missing_guardian_id: str

    # The collection of all contests in the election
    contests: Dict[str, CiphertextPartialDecryptionContest]

    lagrange_coefficient: ElementModQ

    def crypto_hash_with(self, seed_hash: ElementModQ) -> ElementModQ:
        """
        Generates a hash with a given seed that can be checked later against the seed and class metadata.
        """
        ...
