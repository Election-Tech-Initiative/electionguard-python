from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Dict,
    Iterable,
    Iterator,
    Optional,
    List,
    Tuple,
)

from .ballot import CiphertextBallot
from .logs import log_warning


class BallotBoxState(Enum):
    CAST = 1
    SPOILED = 2
    UNKNOWN = 999


# TODO: immutable
@dataclass
class BallotBoxCiphertextBallot(CiphertextBallot):
    state: BallotBoxState = field(default=BallotBoxState.UNKNOWN)


def from_ciphertext_ballot(
    ballot: CiphertextBallot, state: BallotBoxState
) -> BallotBoxCiphertextBallot:
    return BallotBoxCiphertextBallot(
        object_id=ballot.object_id,
        ballot_style=ballot.ballot_style,
        description_hash=ballot.description_hash,
        contests=ballot.contests,
        nonce=ballot.nonce,
        state=state,
    )


class BallotStore(Iterable):
    """
    A representation of a cache of ballots for an election
    """

    _ballot_store: Dict[str, Optional[BallotBoxCiphertextBallot]]

    def __init__(self) -> None:
        self._ballot_store = {}

    def __iter__(self) -> Iterator[BallotBoxCiphertextBallot]:
        return iter(self._ballot_store.values())

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

    def all(self) -> List[BallotBoxCiphertextBallot]:
        """
        Get all `BallotBoxCiphertextBallot` from the store
        """
        return list(self._ballot_store.values())

    def get(self, ballot_id: str) -> Optional[BallotBoxCiphertextBallot]:
        """
        Get a BallotBoxCiphertextBallot from the store if it exists 
        """
        try:
            return self._ballot_store[ballot_id]
        except KeyError:
            return None

    def exists(
        self, ballot_id: str
    ) -> Tuple[bool, Optional[BallotBoxCiphertextBallot]]:
        """
        Check if a specific ballot exists and return it.
        :return: `Tuple[bool, Optional[BallotBoxCiphertextBallot]]`
        """
        existing_ballot = self.get(ballot_id)
        if existing_ballot is None:
            return False, None
        return existing_ballot.state != BallotBoxState.UNKNOWN, existing_ballot
