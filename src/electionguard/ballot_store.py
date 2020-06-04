from collections.abc import Iterable

from typing import (
    Dict,
    Iterable,
    Iterator,
    Optional,
    List,
    Tuple,
)

from .ballot import BallotBoxState, CiphertextBallotBoxBallot
from .logs import log_warning


class BallotStore(Iterable):
    """
    A representation of a cache of ballots for an election
    """

    _ballot_store: Dict[str, Optional[CiphertextBallotBoxBallot]]

    def __init__(self) -> None:
        self._ballot_store = {}

    def __iter__(self) -> Iterator[CiphertextBallotBoxBallot]:
        return iter(self._ballot_store.values())

    def set(
        self, ballot_id: str, ballot: Optional[CiphertextBallotBoxBallot] = None
    ) -> bool:
        """
        Set a specific ballot id to a specific ballot
        """
        if ballot is not None and ballot.state == BallotBoxState.UNKNOWN:
            log_warning(f"cannot add ballot {ballot_id} to store with UNKNOWN state")
            return False
        self._ballot_store[ballot_id] = ballot
        return True

    def all(self) -> List[CiphertextBallotBoxBallot]:
        """
        Get all `CiphertextBallotBoxBallot` from the store
        """
        return list(self._ballot_store.values())

    def get(self, ballot_id: str) -> Optional[CiphertextBallotBoxBallot]:
        """
        Get a CiphertextBallotBoxBallot from the store if it exists
        """
        try:
            return self._ballot_store[ballot_id]
        except KeyError:
            return None

    def exists(
        self, ballot_id: str
    ) -> Tuple[bool, Optional[CiphertextBallotBoxBallot]]:
        """
        Check if a specific ballot exists and return it.
        :return: `Tuple[bool, Optional[CiphertextBallotBoxBallot]]`
        """
        existing_ballot = self.get(ballot_id)
        if existing_ballot is None:
            return False, None
        return existing_ballot.state != BallotBoxState.UNKNOWN, existing_ballot
