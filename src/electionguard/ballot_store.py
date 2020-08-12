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
from .types import BALLOT_ID

# TODO: ISSUE # 74: Remove this class in favor of using DataStore
class BallotStore(Iterable):
    """
    A representation of a cache of ballots for an election
    """

    _ballot_store: Dict[BALLOT_ID, Optional[CiphertextAcceptedBallot]]

    def __init__(self) -> None:
        self._ballot_store = {}

    def __iter__(self) -> Iterator[Optional[CiphertextAcceptedBallot]]:
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
        return [ballot for ballot in self._ballot_store.values() if ballot is not None]

    def get(self, ballot_id: str) -> Optional[CiphertextAcceptedBallot]:
        """
        Get a CiphertextAcceptedBallot from the store if it exists
        """
        if ballot_id in self._ballot_store:
            return self._ballot_store[ballot_id]

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
