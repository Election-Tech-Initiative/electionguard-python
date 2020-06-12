from dataclasses import dataclass
from typing import Dict

from .chaum_pedersen import ChaumPedersenProof
from .election_object_base import ElectionObjectBase

from .group import ElementModP, ElementModQ

from .types import BALLOT_ID, CONTEST_ID, GUARDIAN_ID, SELECTION_ID


@dataclass
class CiphertextDecryptionSelection(ElectionObjectBase):
    """
    A Guardian's Partial Decryption of a selection
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
    A Guardian's Partial Decryption of a contest
    """

    # The ContestDescription Hash
    description_hash: ElementModQ

    # the collection of decryption shares for this contest's selections
    selections: Dict[SELECTION_ID, CiphertextDecryptionSelection]


@dataclass
class CiphertextPartialDecryptionContest(ElectionObjectBase):
    """
    A Ciphertext Partial Decryption contest
    """

    # The ContestDescription Hash
    description_hash: ElementModQ

    # the collection of decryption shares for this contest's selections
    selections: Dict[SELECTION_ID, CiphertextPartialDecryptionSelection]


@dataclass
class BallotDecryptionShare:
    """
    A Guardian's Share of a decryption of a specific ballot
    """

    # The Available Guardian that this share belongs to
    guardian_id: GUARDIAN_ID

    # The Ballot Id that this Decryption Share belongs to
    ballot_id: BALLOT_ID

    # The collection of all contests in the ballot
    contests: Dict[CONTEST_ID, CiphertextDecryptionContest]


@dataclass
class DecryptionShare:
    """
    A Guardian's Share of a decryption of an election
    """

    # The Available Guardian that this share belongs to
    guardian_id: GUARDIAN_ID

    # The collection of all contests in the election
    contests: Dict[CONTEST_ID, CiphertextDecryptionContest]

    spoiled_ballots: Dict[BALLOT_ID, BallotDecryptionShare]


@dataclass
class PartialDecryptionShare:
    """
    A Partial Decryption Share
    """

    # The Available Guardian that this partial share belongs to
    available_guardian_id: GUARDIAN_ID

    # The Missing Guardian for whom this share is calculated on behalf of
    missing_guardian_id: GUARDIAN_ID

    # The collection of all contests in the election
    contests: Dict[CONTEST_ID, CiphertextPartialDecryptionContest]

    lagrange_coefficient: ElementModQ


def get_cast_shares_for_selection(
    selection_id: str, shares: Dict[GUARDIAN_ID, DecryptionShare],
) -> Dict[GUARDIAN_ID, ElementModP]:
    """
    Get the cast shares for a given selection
    """
    cast_shares: Dict[GUARDIAN_ID, ElementModP] = {}
    for share in shares.values():
        for contest in share.contests.values():
            for selection in contest.selections.values():
                if selection.object_id == selection_id:
                    cast_shares[share.guardian_id] = selection.share

    return cast_shares


def get_spoiled_shares_for_selection(
    ballot_id: str, selection_id: str, shares: Dict[GUARDIAN_ID, DecryptionShare],
) -> Dict[GUARDIAN_ID, ElementModP]:
    """
    Get the spoiled shares for a given selection
    """
    spoiled_shares: Dict[GUARDIAN_ID, ElementModP] = {}
    for share in shares.values():
        for ballot in share.spoiled_ballots.values():
            if ballot.ballot_id == ballot_id:
                for contest in ballot.contests.values():
                    for selection in contest.selections.values():
                        if selection.object_id == selection_id:
                            spoiled_shares[share.guardian_id] = selection.share
    return spoiled_shares
