from dataclasses import dataclass, field
from typing import Optional, List, Dict, Set, Tuple
from collections.abc import Container, Sized

from multiprocessing import Pool, cpu_count

from .ballot import BallotBoxState, CiphertextBallotSelection, CiphertextAcceptedBallot
from .ballot_store import BallotStore
from .ballot_validator import ballot_is_valid_for_election
from .election import CiphertextElectionContext, InternalElectionDescription
from .election_object_base import ElectionObjectBase
from .elgamal import ElGamalCiphertext, elgamal_add
from .group import ElementModQ, ONE_MOD_P, ElementModP
from .logs import log_warning

from .types import BALLOT_ID, CONTEST_ID, SELECTION_ID


@dataclass
class PlaintextTallySelection(ElectionObjectBase):
    """
    A plaintext Tally Selection is a decrypted selection of a contest
    """

    plaintext: int
    # g^tally or M in the spec
    value: ElementModP

    message: ElGamalCiphertext


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

    message: ElGamalCiphertext = field(default=ElGamalCiphertext(ONE_MOD_P, ONE_MOD_P))
    """
    The encrypted representation of the total of all ballots for this selection
    """

    def elgamal_accumulate(
        self, elgamal_ciphertext: ElGamalCiphertext
    ) -> ElGamalCiphertext:
        """
        Homomorphically add the specified value to the message
        """
        new_value = elgamal_add(self.message, elgamal_ciphertext)
        self.message = new_value
        return self.message


@dataclass
class PlaintextTallyContest(ElectionObjectBase):
    """
    A plaintext Tally Contest is a collection of plaintext selections
    """

    selections: Dict[SELECTION_ID, PlaintextTallySelection]


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

    tally_selections: Dict[SELECTION_ID, CiphertextTallySelection]
    """
    A collection of CiphertextTallySelection mapped by SelectionDescription.object_id
    """

    def elgamal_accumulate(
        self, contest_selections: List[CiphertextBallotSelection]
    ) -> bool:
        """
        Accumulate the contest selections into this tally
        """

        selection_ids = set(
            [
                selection.object_id
                for selection in contest_selections
                if not selection.is_placeholder_selection
            ]
        )

        if len(contest_selections) == 0:
            log_warning(
                f"accumulate cannot add missing selections for contest {self.object_id}"
            )
            return False

        if any(set(self.tally_selections).difference(selection_ids)):
            log_warning(
                f"accumulate cannot add mismatched selections for contest {self.object_id}"
            )
            return False

        cpu_pool = Pool(cpu_count())

        # iterate through the tally selections and add the new value to the total
        results = cpu_pool.starmap(
            self._accumulate_selections,
            [
                (key, selection_tally, contest_selections)
                for (key, selection_tally) in self.tally_selections.items()
            ],
        )

        cpu_pool.close()

        for (key, ciphertext) in results:
            if ciphertext is None:
                return False
            else:
                self.tally_selections[key].message = ciphertext

        return True

    def _accumulate_selections(
        self,
        key: SELECTION_ID,
        selection_tally: CiphertextTallySelection,
        contest_selections: List[CiphertextBallotSelection],
    ) -> Tuple[SELECTION_ID, Optional[ElGamalCiphertext]]:
        use_selection = None
        for selection in contest_selections:
            if key == selection.object_id:
                use_selection = selection
                break

        # we did not find a selection on the ballot that is required
        # this should never happen when using the `CiphertextTally`
        # but we check anyway
        if not use_selection:
            log_warning(f"add cannot accumulate for missing selection {key}")
            return key, None

        return key, selection_tally.elgamal_accumulate(use_selection.message)


@dataclass
class PlaintextTally(ElectionObjectBase):
    """
    The plaintext representation of all contests in the election
    """

    contests: Dict[CONTEST_ID, PlaintextTallyContest]

    spoiled_ballots: Dict[BALLOT_ID, Dict[CONTEST_ID, PlaintextTallyContest]]


@dataclass
class CiphertextTally(ElectionObjectBase, Container, Sized):
    """
    A `CiphertextTally` accepts cast and spoiled ballots and accumulates a tally on the cast ballots
    """

    _metadata: InternalElectionDescription
    _encryption: CiphertextElectionContext

    # A local cache of ballots id's that have already been cast
    _cast_ballot_ids: Set[BALLOT_ID] = field(init=False)

    cast: Dict[CONTEST_ID, CiphertextTallyContest] = field(init=False)
    """
    A collection of each contest and selection in an election.  
    Retains an encrypted representation of a tally for each selection
    """

    spoiled_ballots: Dict[BALLOT_ID, CiphertextAcceptedBallot] = field(
        default_factory=lambda: {}
    )
    """
    All of the ballots marked spoiled in the election
    """

    def __post_init__(self) -> None:
        object.__setattr__(self, "_cast_ballot_ids", set())
        object.__setattr__(self, "cast", self._build_tally_collection(self._metadata))

    def __len__(self) -> int:
        return len(self._cast_ballot_ids) + len(self.spoiled_ballots)

    def __contains__(self, item: object) -> bool:
        if not isinstance(item, CiphertextAcceptedBallot):
            return False

        if (
            item.object_id in self._cast_ballot_ids
            or item.object_id in self.spoiled_ballots
        ):
            return True

        return False

    def append(self, ballot: CiphertextAcceptedBallot) -> bool:
        """
        Append a ballot to the tally
        """
        if ballot.state == BallotBoxState.UNKNOWN:
            log_warning(f"append cannot add {ballot.object_id} with invalid state")
            return False

        if self.__contains__(ballot):
            log_warning(f"append cannot add {ballot.object_id} that is already tallied")
            return False

        if not ballot_is_valid_for_election(ballot, self._metadata, self._encryption):
            return False

        if ballot.state == BallotBoxState.CAST:
            return self._add_cast(ballot)

        if ballot.state == BallotBoxState.SPOILED:
            return self._add_spoiled(ballot)

        log_warning(f"append cannot add {ballot.object_id}")
        return False

    def count(self) -> int:
        """
        Get a Count of the cast ballots
        """
        return len(self._cast_ballot_ids)

    def _add_cast(self, ballot: CiphertextAcceptedBallot) -> bool:
        """
        Add a cast ballot to the tally
        """

        # iterate through the contests and elgamal add
        for contest in ballot.contests:
            # This should never happen since the ballot is validated against the election metadata
            # but it's possible the local dictionary was modified so we double check.
            if not contest.object_id in self.cast:
                log_warning(
                    f"add cast missing contest in valid set {contest.object_id}"
                )
                return False

            use_contest = self.cast[contest.object_id]
            if not use_contest.elgamal_accumulate(contest.ballot_selections):
                return False

            self.cast[contest.object_id] = use_contest
        self._cast_ballot_ids.add(ballot.object_id)
        return True

    def _add_spoiled(self, ballot: CiphertextAcceptedBallot) -> bool:
        """
        Add a spoiled ballot
        """

        self.spoiled_ballots[ballot.object_id] = ballot
        return True

    def _build_tally_collection(
        self, description: InternalElectionDescription
    ) -> Dict[CONTEST_ID, CiphertextTallyContest]:
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

        return cast_collection


def tally_ballot(
    ballot: CiphertextAcceptedBallot, tally: CiphertextTally
) -> Optional[CiphertextTally]:
    """
    Tally a ballot that is either Cast or Spoiled
    :return: The mutated CiphertextTally or None if there is an error
    """

    if ballot.state == BallotBoxState.UNKNOWN:
        log_warning(
            f"tally ballots error tallying unknown state for ballot {ballot.object_id}"
        )
        return None

    if tally.append(ballot):
        return tally

    return None


def tally_ballots(
    store: BallotStore,
    metadata: InternalElectionDescription,
    context: CiphertextElectionContext,
) -> Optional[CiphertextTally]:
    """
    Tally all of the ballots in the ballot store.
    :return: a CiphertextTally or None if there is an error
    """
    # TODO: ISSUE #14: unique Id for the tally
    tally: CiphertextTally = CiphertextTally("election-results", metadata, context)
    for ballot in store:
        if ballot is None:
            return None
        if tally_ballot(ballot, tally) is None:
            return None
    return tally
