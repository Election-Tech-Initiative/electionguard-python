from typing import Iterable, List, Tuple
from electionguard.scheduler import Scheduler
from electionguard.data_store import DataStore
from electionguard.tally import CiphertextTally
from electionguard.ballot_box import get_ballots
from electionguard.ballot import BallotBoxState, SubmittedBallot

from ..cli_models import BuildElectionResults
from .cli_step_base import CliStepBase


class TallyStep(CliStepBase):
    """Responsible for creating a tally and retrieving spoiled ballots."""

    def get_from_ballots(
        self,
        build_election_results: BuildElectionResults,
        ballots: List[SubmittedBallot],
    ) -> Tuple[CiphertextTally, List[SubmittedBallot]]:
        self.print_header("Creating Tally")
        tuble_ballots = [(None, b) for b in ballots]
        tally = self._get_tally(build_election_results, tuble_ballots)

        spoiled_ballots = [b for b in ballots if b.state == BallotBoxState.SPOILED]

        return (tally, spoiled_ballots)

    def get_from_ballot_store(
        self, build_election_results: BuildElectionResults, ballot_store: DataStore
    ) -> Tuple[CiphertextTally, List[SubmittedBallot]]:
        self.print_header("Creating Tally")
        ciphertext_tally = self._get_tally(build_election_results, ballot_store.items())
        spoiled_ballots = self._get_spoiled_ballots(ballot_store)
        return (ciphertext_tally, spoiled_ballots)

    def _get_tally(
        self,
        build_election_results: BuildElectionResults,
        ballots: Iterable[Tuple[None, SubmittedBallot]],
    ) -> CiphertextTally:
        tally = CiphertextTally(
            "election-results",
            build_election_results.internal_manifest,
            build_election_results.context,
        )
        with Scheduler() as scheduler:
            tally.batch_append(ballots, True, scheduler)
        self.print_value("Ballots in tally", tally.__len__())
        return tally

    def _get_spoiled_ballots(self, ballot_store: DataStore) -> List[SubmittedBallot]:
        submitted_ballots = get_ballots(ballot_store, BallotBoxState.SPOILED)
        spoiled_ballots_list = list(submitted_ballots.values())
        self.print_value("Spoiled ballots", len(spoiled_ballots_list))
        return spoiled_ballots_list
