from dataclasses import dataclass, field
from typing import Optional, List, Dict

from .ballot import CiphertextBallotSelection

from .ballot_store import (
    BallotBoxState,
    BallotBoxCiphertextBallot,
    BallotStore,
)
from .election import CiphertextElectionContext, InternalElectionDescription
from .election_object_base import ElectionObjectBase
from .elgamal import ElGamalCiphertext, elgamal_add, elgamal_homomorphic_zero
from .group import ElementModQ
from .logs import log_warning
from .validity import ballot_is_valid_for_election


@dataclass
class CiphertextTallySelection(ElectionObjectBase):
    """
    a CiphertextTallySelection is a homomorphic accumulation of all of the 
    CiphertextBallotSelection instances for a specific selection in an election.
    """

    description_hash: ElementModQ
    """
    The SelectionDescription hash
    """

    message: ElGamalCiphertext = field(init=False)
    """
    The encrypted representation of the total of all ballots for this selection
    """

    def __post_init__(self) -> None:
        object.__setattr__(self, "message", elgamal_homomorphic_zero())

    def elgamal_accumulate(self, elgamal_ciphertext: ElGamalCiphertext) -> bool:
        """
        Homomorphically add the specified value to the message
        """
        new_value = elgamal_add(*[self.message, elgamal_ciphertext])
        self.message = new_value
        return True


@dataclass
class CiphertextTallyContest(ElectionObjectBase):
    """
    A CiphertextTallyContest is a container for associating a collection of CiphertextTallySelection
    to a specific ContestDescription
    """

    description_hash: ElementModQ
    """
    The ContestDescription hash
    """

    tally_selections: Dict[str, CiphertextTallySelection]
    """
    A collection of CiphertextTallySelection mapped by SelectionDescription.object_id
    """

    def elgamal_accumulate(
        self, contest_selections: List[CiphertextBallotSelection]
    ) -> bool:

        if len(contest_selections) == 0:
            log_warning(
                f"add cannot add an empty collection for contest {self.object_id}"
            )
            return False

        # iterate through the tally selections and add the new value to the total
        for key, selection_tally in self.tally_selections.items():
            use_selection = None
            for selection in contest_selections:
                if key == selection.object_id:
                    use_selection = selection
                    break

            # we did not find a selection on the ballot that is required
            if not use_selection:
                log_warning(
                    f"add cannot accumulate for missing selection {selection.object_id}"
                )
                return False

            if not selection_tally.elgamal_accumulate(use_selection.message):
                return False

        return True


@dataclass
class CiphertextTally(ElectionObjectBase):
    """
    """

    _metadata: InternalElectionDescription
    _encryption: CiphertextElectionContext

    cast: Dict[str, CiphertextTallyContest] = field(init=False)
    spoiled_ballots: Dict[str, BallotBoxCiphertextBallot] = field(
        default_factory=lambda: {}
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "cast", self._build_tally_collection(self._metadata))

    def add_cast(self, ballot: BallotBoxCiphertextBallot) -> bool:
        """
        adda cast ballot to the tally
        """
        if ballot.state != BallotBoxState.CAST:
            log_warning(f"add cast ballots cannot add {ballot.object_id}")
            return False

        if not ballot_is_valid_for_election(ballot, self._metadata, self._encryption):
            return False

        # iterate through the contests and elgamal add
        for contest in ballot.contests:
            use_contest = None
            try:
                use_contest = self.cast[contest.object_id]
            except KeyError:
                # This should never happen since the ballot is validated against the election metadata
                # but it's possible the local dictionary was modified so we double check.
                log_warning(
                    f"add cast missing contest in valid set {contest.object_id}"
                )
                return False

            if not use_contest.elgamal_accumulate(contest.ballot_selections):
                return False

            self.cast[contest.object_id] = use_contest

        return True

    def add_spoiled(self, ballot: BallotBoxCiphertextBallot) -> bool:
        """
        Add a spoiled ballot
        """
        if ballot.state != BallotBoxState.SPOILED:
            log_warning(f"spoiled ballots cannot add {ballot.object_id}")
            return False

        if not ballot_is_valid_for_election(ballot, self._metadata, self._encryption):
            return False

        try:
            if self.spoiled_ballots[ballot.object_id]:
                log_warning(f"spoiled ballot {ballot.object_id} is already tallied")
                return False
        except KeyError:
            pass

        self.spoiled_ballots[ballot.object_id] = ballot
        return True

    def _build_tally_collection(
        self, description: InternalElectionDescription
    ) -> Dict[str, CiphertextTallyContest]:
        """
        Build the object graph for the tally from the InternalElectionDescription
        """

        cast_collection: Dict[str, CiphertextTallyContest] = {}
        for contest in description.contests:
            # build a collection of valid selections for the contest description
            # note: we explicitly ignore the Placeholder Selections.
            contest_selections: Dict[str, CiphertextTallySelection] = {}
            for selection in contest.ballot_selections:
                contest_selections[selection.object_id] = CiphertextTallySelection(
                    selection.object_id, selection.crypto_hash()
                )

            cast_collection[contest.object_id] = CiphertextTallyContest(
                contest.object_id, contest.crypto_hash(), contest_selections
            )

        log_warning(f"built collection: {cast_collection}")

        return cast_collection


def tally_ballot(
    ballot: BallotBoxCiphertextBallot, tally: CiphertextTally
) -> Optional[CiphertextTally]:
    """
    Tally a ballt that is either Cast or Spoiled
    :return: The mutated CiphertextTally or None if there is an error
    """

    log_warning(f"tallying: {ballot.object_id}")

    if ballot.state == BallotBoxState.CAST:
        if not tally.add_cast(ballot):
            return None
    elif ballot.state == BallotBoxState.SPOILED:
        if not tally.add_spoiled(ballot):
            return None
    elif ballot.state == BallotBoxState.UNKNOWN:
        log_warning(
            f"tally ballots error tallying unknown state for ballot {ballot.object_id}"
        )
        return None
    else:
        return None

    return tally


def tally_ballots(
    store: BallotStore,
    metadata: InternalElectionDescription,
    encryption_context: CiphertextElectionContext,
) -> Optional[CiphertextTally]:
    """
    Tally all of the ballots in the ballot store.
    :return: a ciphertextTally or None if there is an error
    """
    # TODO: unique Id
    tally: CiphertextTally = CiphertextTally(
        "election-results", metadata, encryption_context
    )
    for ballot in store:
        if tally_ballot(ballot, tally) is None:
            return None
    return tally
