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


@dataclass
class BallotBoxCiphertextBallot(CyphertextBallot):
    state: BallotBoxState = field(default=BallotBoxState.UNKNOWN)


class BallotStore:
    _ballot_store: Dict[str, Optional[BallotBoxCiphertextBallot]]

    def set(
        self, ballot_id: str, ballot: Optional[BallotBoxCiphertextBallot] = None
    ) -> bool:
        if ballot is not None and ballot.state == BallotBoxState.UNKNOWN:
            log_warning(f"cannot add ballot {ballot_id} to store with UNKNOWN state")
            return False
        self._ballot_store[ballot_id] = ballot
        return True

    def get(self, ballot_id: str) -> Optional[BallotBoxCiphertextBallot]:
        return self._ballot_store[ballot_id]

    def exists(self, ballot_id) -> Tuple[bool, Optional[BallotBoxCiphertextBallot]]:
        existing_ballot = self.get(ballot_id)
        if existing_ballot is None:
            return False, None
        return existing_ballot.state != BallotBoxState.UNKNOWN, existing_ballot


@dataclass
class BallotBox(object):
    _metadata: InternalElectionDescription
    _encryption: CyphertextElection
    _store: BallotStore

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

    # TODO: check if the ballot includes the nonce, and possibly regenerate the proofs
    # TODO: check if the ballot includes the tracking code and regenerate it if missing

    ballot_exists, existing_ballot = store.exists(ballot.object_id)
    if ballot_exists and existing_ballot is not None:
        log_warning(
            f"error casting ballot, {ballot.object_id} already exists with state: {existing_ballot.state}"
        )
        return None


def spoil_ballot(
    ballot: CyphertextBallot,
    metadata: InternalElectionDescription,
    encryption_context: CyphertextElection,
    store: BallotStore,
) -> Optional[BallotBoxCiphertextBallot]:
    if not ballot_is_valid_for_election(ballot, metadata, encryption_context):
        log_warning("error in spoil_ballot: ballot is not valid for the election")
        return None


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
