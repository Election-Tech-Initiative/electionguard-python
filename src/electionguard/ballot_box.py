from dataclasses import dataclass, field
from typing import Dict, Optional

from .ballot import (
    BallotBoxState,
    CiphertextBallot,
    SubmittedBallot,
    from_ciphertext_ballot,
)
from .ballot_validator import ballot_is_valid_for_election
from .data_store import DataStore
from .election import CiphertextElectionContext
from .logs import log_warning
from .manifest import InternalManifest
from .types import BALLOT_ID


@dataclass
class BallotBox:
    """
    A stateful convenience wrapper to cache election data
    """

    _internal_manifest: InternalManifest = field()
    _encryption: CiphertextElectionContext = field()
    _store: DataStore = field(default_factory=lambda: DataStore())

    def cast(self, ballot: CiphertextBallot) -> Optional[SubmittedBallot]:
        """
        Cast a specific encrypted `CiphertextBallot`
        """
        return accept_ballot(
            ballot,
            BallotBoxState.CAST,
            self._internal_manifest,
            self._encryption,
            self._store,
        )

    def spoil(self, ballot: CiphertextBallot) -> Optional[SubmittedBallot]:
        """
        Spoil a specific encrypted `CiphertextBallot`
        """
        return accept_ballot(
            ballot,
            BallotBoxState.SPOILED,
            self._internal_manifest,
            self._encryption,
            self._store,
        )


def accept_ballot(
    ballot: CiphertextBallot,
    state: BallotBoxState,
    internal_manifest: InternalManifest,
    context: CiphertextElectionContext,
    store: DataStore,
) -> Optional[SubmittedBallot]:
    """
    Submit a ballot within the context of a specified election and against an existing data store
    Verified that the ballot is valid for the election `internal_manifest` and `context` and
    that the ballot has not already been cast or spoiled.
    :return: a `SubmittedBallot` or `None` if there was an error
    """
    if not ballot_is_valid_for_election(ballot, internal_manifest, context):
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


def get_ballots(
    store: DataStore, state: Optional[BallotBoxState]
) -> Dict[BALLOT_ID, SubmittedBallot]:
    return {
        ballot_id: ballot
        for (ballot_id, ballot) in store.items()
        if state is None or ballot.state == state
    }
