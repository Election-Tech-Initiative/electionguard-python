from collections.abc import Iterable

from typing import (
    Dict,
    Iterable,
    Iterator,
    Optional,
    List,
    Tuple,
)

from .ballot import BallotBoxState, CiphertextAcceptedBallot
from .logs import log_warning

BallotId = str


class BallotStore(Iterable):
    """
    A representation of a cache of ballots for an election
    """

    _ballot_store: Dict[BallotId, Optional[CiphertextAcceptedBallot]]

    def __init__(self) -> None:
        self._ballot_store = {}

    def __iter__(self) -> Iterator[CiphertextAcceptedBallot]:
        return iter(self._ballot_store.values())

    def set(
        self, ballot_id: str, ballot: Optional[CiphertextAcceptedBallot] = None
    ) -> bool:
        """
        Set a specific ballot id to a specific ballot
        """
        if ballot is not None and ballot.state == BallotBoxState.UNKNOWN:
            log_warning(f"cannot add ballot {ballot_id} to store with UNKNOWN state")
            return False
        self._ballot_store[ballot_id] = ballot
        return True

    def all(self) -> List[CiphertextAcceptedBallot]:
        """
        Get all `CiphertextAcceptedBallot` from the store
        """
        return list(self._ballot_store.values())

    def get(self, ballot_id: str) -> Optional[CiphertextAcceptedBallot]:
        """
        Get a CiphertextAcceptedBallot from the store if it exists
        """
        try:
            return self._ballot_store[ballot_id]
        except KeyError:
            return None

    def exists(self, ballot_id: str) -> Tuple[bool, Optional[CiphertextAcceptedBallot]]:
        """
        Check if a specific ballot exists and return it.
        :return: `Tuple[bool, Optional[CiphertextAcceptedBallot]]`
        """
        existing_ballot = self.get(ballot_id)
        if existing_ballot is None:
            return False, None
        return existing_ballot.state != BallotBoxState.UNKNOWN, existing_ballot
