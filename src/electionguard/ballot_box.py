from dataclasses import dataclass, field
from typing import Optional

from .ballot import (
    BallotBoxState,
    CiphertextBallot,
    CiphertextAcceptedBallot,
    from_ciphertext_ballot,
)
from .data_store import DataStore

from .election import CiphertextElectionContext, InternalElectionDescription
from .logs import log_warning
from .ballot_validator import ballot_is_valid_for_election


@dataclass
class BallotBox(object):
    """
    A stateful convenience wrapper to cache election data
    """

    _metadata: InternalElectionDescription = field()
    _encryption: CiphertextElectionContext = field()
    _store: DataStore = field(default_factory=lambda: DataStore())

    def cast(self, ballot: CiphertextBallot) -> Optional[CiphertextAcceptedBallot]:
        """
        Cast a specific encrypted `CiphertextBallot`
        """
        return accept_ballot(
            ballot, BallotBoxState.CAST, self._metadata, self._encryption, self._store
        )

    def spoil(self, ballot: CiphertextBallot) -> Optional[CiphertextAcceptedBallot]:
        """
        Spoil a specific encrypted `CiphertextBallot`
        """
        return accept_ballot(
            ballot,
            BallotBoxState.SPOILED,
            self._metadata,
            self._encryption,
            self._store,
        )


def accept_ballot(
    ballot: CiphertextBallot,
    state: BallotBoxState,
    metadata: InternalElectionDescription,
    context: CiphertextElectionContext,
    store: DataStore,
) -> Optional[CiphertextAcceptedBallot]:
    """
    Accept a ballot within the context of a specified election and against an existing data store
    Verified that the ballot is valid for the election `metadata` and `context` and
    that the ballot has not already been cast or spoiled.
    :return: a `CiphertextAcceptedBallot` or `None` if there was an error
    """
    if not ballot_is_valid_for_election(ballot, metadata, context):
        return None

    existing_ballot = store.get(ballot.object_id)
    if existing_ballot is not None:
        log_warning(
            f"error accepting ballot, {ballot.object_id} already exists with state: {existing_ballot.state}"
        )
        return None

    # TODO: ISSUE #56: check if the ballot includes the nonce, and regenerate the proofs
    # TODO: ISSUE #56: check if the ballot includes the proofs, if it does not include the nonce

    ballot_box_ballot = from_ciphertext_ballot(ballot, state)

    store.set(ballot_box_ballot.object_id, ballot_box_ballot)
    return store.get(ballot_box_ballot.object_id)
