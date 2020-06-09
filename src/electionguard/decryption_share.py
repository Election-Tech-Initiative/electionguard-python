from dataclasses import dataclass
from typing import Dict

from .chaum_pedersen import ChaumPedersenProof
from .election_object_base import ElectionObjectBase

from .group import ElementModP, ElementModQ


@dataclass
class CiphertextDecryptionSelection(ElectionObjectBase):
    """
    A Ciphertext Decryption Selection
    """

    # The SelectionDescription hash
    description_hash: ElementModQ

    # M_i in the spec
    share: ElementModP

    # Proof that the share was decrypted correctly
    proof: ChaumPedersenProof


@dataclass
class CiphertextPartialDecryptionSelection(ElectionObjectBase):
    """
    A Cipertext Partial Decryption Selection
    """

    # The SelectionDescription hash
    description_hash: ElementModQ

    # M_i in the spec
    partial_share: ElementModP

    # Proof that the share was decrypted correctly
    proof: ChaumPedersenProof


@dataclass
class CiphertextDecryptionContest(ElectionObjectBase):
    """
    A ciphertext Decryption contest
    """

    # The ContestDescription Hash
    description_hash: ElementModQ

    # the collection of decryption shares for this contest's selections
    selections: Dict[str, CiphertextDecryptionSelection]


@dataclass
class CiphertextPartialDecryptionContest(ElectionObjectBase):
    """
    A Ciphertext Partial Decryption contest
    """

    # The ContestDescription Hash
    description_hash: ElementModQ

    # the collection of decryption shares for this contest's selections
    selections: Dict[str, CiphertextPartialDecryptionSelection]


@dataclass
class DecryptionShare:
    """
    A Decryption Share
    """

    # The Available Guardian that this share belongs to
    guardian_id: str

    # The collection of all contests in the election
    contests: Dict[str, CiphertextDecryptionContest]


@dataclass
class PartialDecryptionShare:
    """
    A Partial Decryption Share
    """

    # The Available Guardian that this partial share belongs to
    available_guardian_id: str

    # The Missing Guardian for whom this share is calculated on behalf of
    missing_guardian_id: str

    # The collection of all contests in the election
    contests: Dict[str, CiphertextPartialDecryptionContest]

    lagrange_coefficient: ElementModQ
