# pylint: disable=unnecessary-comprehension
from dataclasses import dataclass, field
from typing import Iterable, Optional, List, Dict, Set, Tuple, Any
from collections.abc import Container, Sized

from .ballot import (
    BallotBoxState,
    CiphertextBallotSelection,
    SubmittedBallot,
    CiphertextSelection,
)
from .data_store import DataStore
from .ballot_validator import ballot_is_valid_for_election
from .decryption_share import CiphertextDecryptionSelection
from .election import CiphertextElectionContext
from .election_object_base import ElectionObjectBase
from .elgamal import ElGamalCiphertext, elgamal_add
from .group import ElementModQ, ONE_MOD_P, ElementModP
from .logs import log_warning
from .manifest import InternalManifest
from .scheduler import Scheduler
from .types import BALLOT_ID, CONTEST_ID, SELECTION_ID


@dataclass
class PlaintextTallySelection(ElectionObjectBase):
    """
    A plaintext Tally Selection is a decrypted selection of a contest
    """

    tally: int
    # g^tally or M in the spec
    value: ElementModP

    message: ElGamalCiphertext

    shares: List[CiphertextDecryptionSelection]


@dataclass
class CiphertextTallySelection(ElectionObjectBase, CiphertextSelection):
    """
    a CiphertextTallySelection is a homomorphic accumulation of all of the
    CiphertextBallotSelection instances for a specific selection in an election.
    """

    description_hash: ElementModQ
    """
    The SelectionDescription hash
    """

    ciphertext: ElGamalCiphertext = field(
        default=ElGamalCiphertext(ONE_MOD_P, ONE_MOD_P)
    )
    """
    The encrypted representation of the total of all ballots for this selection
    """

    def elgamal_accumulate(
        self, elgamal_ciphertext: ElGamalCiphertext
    ) -> ElGamalCiphertext:
        """
        Homomorphically add the specified value to the message
        """
        new_value = elgamal_add(self.ciphertext, elgamal_ciphertext)
        self.ciphertext = new_value
        return self.ciphertext


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

    selections: Dict[SELECTION_ID, CiphertextTallySelection]
    """
    A collection of CiphertextTallySelection mapped by SelectionDescription.object_id
    """

    def accumulate_contest(
        self,
        contest_selections: List[CiphertextBallotSelection],
        scheduler: Optional[Scheduler] = None,
    ) -> bool:
        """
        Accumulate the contest selections of an individual ballot into this tally
        """

        if len(contest_selections) == 0:
            log_warning(
                f"accumulate cannot add missing selections for contest {self.object_id}"
            )
            return False

        # Validate the input data by comparing the selection id's provided
        # to the valid selection id's for this tally contest
        selection_ids = {
            selection.object_id
            for selection in contest_selections
            if not selection.is_placeholder_selection
        }

        if any(set(self.selections).difference(selection_ids)):
            log_warning(
                f"accumulate cannot add mismatched selections for contest {self.object_id}"
            )
            return False

        if scheduler is None:
            scheduler = Scheduler()

        # iterate through the tally selections and add the new value to the total
        results: List[
            Tuple[SELECTION_ID, Optional[ElGamalCiphertext]]
        ] = scheduler.schedule(
            self._accumulate_selections,
            [
                (key, selection_tally, contest_selections)
                for (key, selection_tally) in self.selections.items()
            ],
        )

        for (key, ciphertext) in results:
            if ciphertext is None:
                return False
            self.selections[key].ciphertext = ciphertext

        return True

    @staticmethod
    def _accumulate_selections(
        key: SELECTION_ID,
        selection_tally: CiphertextTallySelection,
        contest_selections: List[CiphertextBallotSelection],
    ) -> Tuple[SELECTION_ID, Optional[ElGamalCiphertext]]:
        use_selection = None
        for selection in contest_selections:
            if key == selection.object_id:
                use_selection = selection
                break

        # a selection on the ballot that is required was not found
        # this should never happen when using the `CiphertextTally`
        # but sanity check anyway
        if not use_selection:
            log_warning(f"add cannot accumulate for missing selection {key}")
            return key, None

        return key, selection_tally.elgamal_accumulate(use_selection.ciphertext)


@dataclass
class PlaintextTally(ElectionObjectBase):
    """
    The plaintext representation of all contests in the election
    """

    contests: Dict[CONTEST_ID, PlaintextTallyContest]


@dataclass
class PublishedCiphertextTally(ElectionObjectBase):
    """
    A published version of the ciphertext tally
    """

    contests: Dict[CONTEST_ID, CiphertextTallyContest]


@dataclass
class CiphertextTally(ElectionObjectBase, Container, Sized):
    """
    A `CiphertextTally` accepts cast and spoiled ballots and accumulates a tally on the cast ballots
    """

    _internal_manifest: InternalManifest
    _encryption: CiphertextElectionContext

    # A local cache of ballots id's that have already been cast
    _cast_ballot_ids: Set[BALLOT_ID] = field(init=False)
    _spoiled_ballot_ids: Set[BALLOT_ID] = field(init=False)

    contests: Dict[CONTEST_ID, CiphertextTallyContest] = field(init=False)
    """
    A collection of each contest and selection in an election.
    Retains an encrypted representation of a tally for each selection
    """

    def __post_init__(self) -> None:
        object.__setattr__(self, "_cast_ballot_ids", set())
        object.__setattr__(self, "_spoiled_ballot_ids", set())
        object.__setattr__(
            self, "contests", self._build_tally_collection(self._internal_manifest)
        )

    def __len__(self) -> int:
        return len(self._cast_ballot_ids) + len(self._spoiled_ballot_ids)

    def __contains__(self, item: object) -> bool:
        if not isinstance(item, SubmittedBallot):
            return False

        if (
            item.object_id in self._cast_ballot_ids
            or item.object_id in self._spoiled_ballot_ids
        ):
            return True

        return False

    def append(
        self, ballot: SubmittedBallot, scheduler: Optional[Scheduler] = None
    ) -> bool:
        """
        Append a ballot to the tally and recalculate the tally.
        """
        if ballot.state == BallotBoxState.UNKNOWN:
            log_warning(f"append cannot add {ballot.object_id} with invalid state")
            return False

        if self.__contains__(ballot):
            log_warning(f"append cannot add {ballot.object_id} that is already tallied")
            return False

        if not ballot_is_valid_for_election(
            ballot, self._internal_manifest, self._encryption
        ):
            return False

        if ballot.state == BallotBoxState.CAST:
            return self._add_cast(ballot, scheduler)

        if ballot.state == BallotBoxState.SPOILED:
            return self._add_spoiled(ballot)

        log_warning(f"append cannot add {ballot.object_id}")
        return False

    def batch_append(
        self,
        ballots: Iterable[Tuple[Any, SubmittedBallot]],
        scheduler: Optional[Scheduler] = None,
    ) -> bool:
        """
        Append a collection of Ballots to the tally and recalculate
        """
        cast_ballot_selections: Dict[
            SELECTION_ID, Dict[BALLOT_ID, ElGamalCiphertext]
        ] = {}
        for ballot in ballots:
            # get the value of the dict
            ballot_value = ballot[1]
            if not self.__contains__(ballot) and ballot_is_valid_for_election(
                ballot_value, self._internal_manifest, self._encryption
            ):
                if ballot_value.state == BallotBoxState.CAST:

                    # collect the selections so they can can be accumulated in parallel
                    for contest in ballot_value.contests:
                        for selection in contest.ballot_selections:
                            if selection.object_id not in cast_ballot_selections:
                                cast_ballot_selections[selection.object_id] = {}

                            cast_ballot_selections[selection.object_id][
                                ballot_value.object_id
                            ] = selection.ciphertext

                # just append the spoiled ballots
                elif ballot_value.state == BallotBoxState.SPOILED:
                    self._add_spoiled(ballot_value)

        # cache the cast ballot id's so they are not double counted
        if self._execute_accumulate(cast_ballot_selections, scheduler):
            for ballot in ballots:
                # get the value of the dict
                ballot_value = ballot[1]
                if ballot_value.state == BallotBoxState.CAST:
                    self._cast_ballot_ids.add(ballot_value.object_id)
            return True

        return False

    def cast(self) -> int:
        """
        Get a count of the cast ballots
        """
        return len(self._cast_ballot_ids)

    def spoiled(self) -> int:
        """
        Get a count of the spoiled ballots
        """
        return len(self._spoiled_ballot_ids)

    def publish(self) -> PublishedCiphertextTally:
        return PublishedCiphertextTally(self.object_id, self.contests)

    @staticmethod
    def _accumulate(
        id: str, ballot_selections: Dict[BALLOT_ID, ElGamalCiphertext]
    ) -> Tuple[str, ElGamalCiphertext]:
        return (
            id,
            elgamal_add(*[ciphertext for ciphertext in ballot_selections.values()]),
        )

    def _add_cast(
        self, ballot: SubmittedBallot, scheduler: Optional[Scheduler] = None
    ) -> bool:
        """
        Add a cast ballot to the tally, synchronously
        """

        # iterate through the contests and elgamal add
        for contest in ballot.contests:
            # This should never happen since the ballot is validated against the election metadata
            # but it's possible the local dictionary was modified so we double check.
            if not contest.object_id in self.contests:
                log_warning(
                    f"add cast missing contest in valid set {contest.object_id}"
                )
                return False

            use_contest = self.contests[contest.object_id]
            if not use_contest.accumulate_contest(contest.ballot_selections, scheduler):
                return False

            self.contests[contest.object_id] = use_contest
        self._cast_ballot_ids.add(ballot.object_id)
        return True

    def _add_spoiled(self, ballot: SubmittedBallot) -> bool:
        """
        Add a spoiled ballot
        """

        self._spoiled_ballot_ids.add(ballot.object_id)
        return True

    @staticmethod
    def _build_tally_collection(
        internal_manifest: InternalManifest,
    ) -> Dict[CONTEST_ID, CiphertextTallyContest]:
        """
        Build the object graph for the tally from the InternalManifest
        """

        cast_collection: Dict[str, CiphertextTallyContest] = {}
        for contest in internal_manifest.contests:
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

    def _execute_accumulate(
        self,
        ciphertext_selections_by_selection_id: Dict[
            str, Dict[BALLOT_ID, ElGamalCiphertext]
        ],
        scheduler: Optional[Scheduler] = None,
    ) -> bool:

        result_set: List[Tuple[SELECTION_ID, ElGamalCiphertext]]
        if not scheduler:
            scheduler = Scheduler()
        result_set = scheduler.schedule(
            self._accumulate,
            [
                (selection_id, selections)
                for (
                    selection_id,
                    selections,
                ) in ciphertext_selections_by_selection_id.items()
            ],
        )

        result_dict = {
            selection_id: ciphertext for (selection_id, ciphertext) in result_set
        }

        for contest in self.contests.values():
            for selection_id, selection in contest.selections.items():
                if selection_id in result_dict:
                    selection.elgamal_accumulate(result_dict[selection_id])

        return True


def tally_ballot(
    ballot: SubmittedBallot, tally: CiphertextTally
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
    store: DataStore,
    internal_manifest: InternalManifest,
    context: CiphertextElectionContext,
) -> Optional[CiphertextTally]:
    """
    Tally all of the ballots in the ballot store.
    :return: a CiphertextTally or None if there is an error
    """
    # TODO: ISSUE #14: unique Id for the tally
    tally: CiphertextTally = CiphertextTally(
        "election-results", internal_manifest, context
    )
    if tally.batch_append(store):
        return tally
    return None
