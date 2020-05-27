from dataclasses import dataclass, field, InitVar
from enum import Enum
from typing import Dict, Optional, List, Tuple

from .ballot import (
    CyphertextBallot,
    CyphertextBallotContest,
    CyphertextBallotSelection,
    PlaintextBallot,
    PlaintextBallotContest,
    PlaintextBallotSelection,
    hashed_ballot_nonce,
)

from .election import (
    BallotStyle,
    CyphertextElection,
    InternalElectionDescription,
    ContestDescription,
    ContestDescriptionWithPlaceholders,
    SelectionDescription,
)

from .logs import log_warning
from .nonces import Nonces
from .utils import unwrap_optional


class BallotBoxState(Enum):
    CAST = 1
    SPOILED = 2
    UNKNOWN = 999


# TODO: immutable
@dataclass
class BallotBoxCiphertextBallot(CyphertextBallot):
    state: BallotBoxState = field(default=BallotBoxState.UNKNOWN)


def from_ciphertext_ballot(ballot: CyphertextBallot) -> BallotBoxCiphertextBallot:
    return BallotBoxCiphertextBallot(
        object_id=ballot.object_id,
        ballot_style=ballot.ballot_style,
        description_hash=ballot.description_hash,
        contests=ballot.contests,
        nonce=ballot.nonce,
    )


class BallotStore:
    """
    A representation of a cache of ballots for an election
    """

    _ballot_store: Dict[str, Optional[BallotBoxCiphertextBallot]]

    def __init__(self) -> None:
        self._ballot_store = {}

    def set(
        self, ballot_id: str, ballot: Optional[BallotBoxCiphertextBallot] = None
    ) -> bool:
        """
        Set a specific ballot id to a specific ballot
        """
        if ballot is not None and ballot.state == BallotBoxState.UNKNOWN:
            log_warning(f"cannot add ballot {ballot_id} to store with UNKNOWN state")
            return False
        self._ballot_store[ballot_id] = ballot
        return True

    def get(self, ballot_id: str) -> Optional[BallotBoxCiphertextBallot]:
        try:
            return self._ballot_store[ballot_id]
        except KeyError:
            return None

    def exists(
        self, ballot_id: str
    ) -> Tuple[bool, Optional[BallotBoxCiphertextBallot]]:
        existing_ballot = self.get(ballot_id)
        if existing_ballot is None:
            return False, None
        return existing_ballot.state != BallotBoxState.UNKNOWN, existing_ballot


@dataclass
class BallotBox(object):
    """
    A stateful convenience wrapper to cache election data
    """

    _metadata: InternalElectionDescription = field()
    _encryption: CyphertextElection = field()
    _store: BallotStore = field()

    def cast(self, ballot: CyphertextBallot) -> Optional[BallotBoxCiphertextBallot]:
        return cast_ballot(ballot, self._metadata, self._encryption, self._store)

    def spoil(self, ballot: CyphertextBallot) -> Optional[BallotBoxCiphertextBallot]:
        return spoil_ballot(ballot, self._metadata, self._encryption, self._store)


def cast_ballot(
    ballot: CyphertextBallot,
    metadata: InternalElectionDescription,
    encryption_context: CyphertextElection,
    store: BallotStore,
) -> Optional[BallotBoxCiphertextBallot]:
    if not ballot_is_valid_for_election(ballot, metadata, encryption_context):
        log_warning("error in cast_ballot: ballot is not valid for the election")
        return None

    ballot_exists, existing_ballot = store.exists(ballot.object_id)
    if ballot_exists and existing_ballot is not None:
        log_warning(
            f"error casting ballot, {ballot.object_id} already exists with state: {existing_ballot.state}"
        )
        return None

    # TODO: check if the ballot includes the nonce, and possibly regenerate the proofs
    # TODO: check if the ballot includes the proofs, if it does not include the nonce
    # TODO: check if the ballot includes the tracking code and regenerate it if missing

    # check the ballot is well-formed
    # Cheeck the proofs

    ballot_box_ballot = from_ciphertext_ballot(ballot)
    ballot_box_ballot.state = BallotBoxState.CAST

    store.set(ballot_box_ballot.object_id, ballot_box_ballot)
    return store.get(ballot_box_ballot.object_id)


def spoil_ballot(
    ballot: CyphertextBallot,
    metadata: InternalElectionDescription,
    encryption_context: CyphertextElection,
    store: BallotStore,
) -> Optional[BallotBoxCiphertextBallot]:
    """
    """
    if not ballot_is_valid_for_election(ballot, metadata, encryption_context):
        log_warning("error in spoil_ballot: ballot is not valid for the election")
        return None

    ballot_exists, existing_ballot = store.exists(ballot.object_id)
    if ballot_exists and existing_ballot is not None:
        log_warning(
            f"error spoiling ballot, {ballot.object_id} already exists with state: {existing_ballot.state}"
        )
        return None

    # TODO: check if the ballot includes the nonce, and possibly regenerate the proofs
    # TODO: check if the ballot includes the proofs, if it does not include the nonce
    # TODO: check if the ballot includes the tracking code and regenerate it if missing

    # check the ballot is well-formed
    # Cheeck the proofs

    ballot_box_ballot = from_ciphertext_ballot(ballot)
    ballot_box_ballot.state = BallotBoxState.SPOILED

    store.set(ballot_box_ballot.object_id, ballot_box_ballot)
    return store.get(ballot_box_ballot.object_id)


def ballot_is_valid_for_election(
    ballot: CyphertextBallot,
    metadata: InternalElectionDescription,
    encryption_context: CyphertextElection,
) -> bool:

    if not ballot_is_valid_for_style(
        ballot, metadata.get_ballot_style(ballot.ballot_style)
    ):
        log_warning(
            "error in ballot_is_valid_for_election: mismatching ballot selections"
        )
        return False

    if not ballot.is_valid_encryption(
        encryption_context.crypto_extended_base_hash,
        encryption_context.elgamal_public_key,
    ):
        log_warning(
            "error in ballot_is_valid_for_election: mismatching ballot encryption"
        )
        return False

    return True


def ballot_is_valid_for_style(ballot: CyphertextBallot, style: BallotStyle) -> bool:
    return True
