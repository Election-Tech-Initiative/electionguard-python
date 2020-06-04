from dataclasses import dataclass, field
from typing import Optional

from .ballot import (
    BallotBoxState,
    CiphertextBallot,
    CiphertextBallotBoxBallot,
    from_ciphertext_ballot,
)
from .ballot_store import BallotStore

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
    _store: BallotStore = field()

    def cast(self, ballot: CiphertextBallot) -> Optional[CiphertextBallotBoxBallot]:
        """
        cast a specific encrypted `CiphertextBallot`
        """
        return cast_ballot(ballot, self._metadata, self._encryption, self._store)

    def spoil(self, ballot: CiphertextBallot) -> Optional[CiphertextBallotBoxBallot]:
        """
        spoil a specific encrypted `CiphertextBallot`
        """
        return spoil_ballot(ballot, self._metadata, self._encryption, self._store)


def cast_ballot(
    ballot: CiphertextBallot,
    metadata: InternalElectionDescription,
    encryption_context: CiphertextElectionContext,
    store: BallotStore,
) -> Optional[CiphertextBallotBoxBallot]:
    """
    Cast a ballot within the context of a specified election and against an existing data store
    Verified that the ballot is valid for the election `metadata` and `encryption_context` and
    that the ballot has not already been cast or spoiled.
    :return: a `CiphertextBallotBoxBallot` or `None` if there was an error
    """
    if not ballot_is_valid_for_election(ballot, metadata, encryption_context):
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

    ballot_box_ballot = from_ciphertext_ballot(ballot, BallotBoxState.CAST)

    store.set(ballot_box_ballot.object_id, ballot_box_ballot)
    return store.get(ballot_box_ballot.object_id)


def spoil_ballot(
    ballot: CiphertextBallot,
    metadata: InternalElectionDescription,
    encryption_context: CiphertextElectionContext,
    store: BallotStore,
) -> Optional[CiphertextBallotBoxBallot]:
    """
    Spoil a ballot within the context of a specified election and against an existing data store
    Verified that the ballot is valid for the election `metadata` and `encryption_context` and
    that the ballot has not already been cast or spoiled.
    :return: a `CiphertextBallotBoxBallot` or `None` if there was an error
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

    ballot_box_ballot = from_ciphertext_ballot(ballot, BallotBoxState.SPOILED)

    store.set(ballot_box_ballot.object_id, ballot_box_ballot)
    return store.get(ballot_box_ballot.object_id)
