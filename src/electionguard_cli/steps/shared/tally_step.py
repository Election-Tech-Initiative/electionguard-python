from typing import List, Tuple
from electionguard.scheduler import Scheduler
from electionguard.utils import get_optional
from electionguard.data_store import DataStore
from electionguard.tally import CiphertextTally, tally_ballots
from electionguard.ballot_box import get_ballots
from electionguard.ballot import BallotBoxState, SubmittedBallot

from electionguard_cli.cli_models import BuildElectionResults
from electionguard_cli.steps.import_ballots import ImportBallotsInputRetrievalStep
from electionguard_cli.steps.shared import CliStepBase


class TallyStep(CliStepBase):
    """Responsible for creating a tally and retrieving spoiled ballots."""

    def create_tally(
        self,
        election_inputs: ImportBallotsInputRetrievalStep,
        build_election_results: BuildElectionResults,
    ) -> Tuple[CiphertextTally, List[SubmittedBallot]]:
        self.print_header("Creating Tally")
        tally = CiphertextTally(
            "ciphertext_tally",
            build_election_results.internal_manifest,
            build_election_results.context,
        )
        ballots = [(None, b) for b in election_inputs.submitted_ballots]
        with Scheduler() as scheduler:
            tally.batch_append(ballots, scheduler)

        spoiled_ballots = [
            b
            for b in election_inputs.submitted_ballots
            if b.state == BallotBoxState.SPOILED
        ]

        return (tally, spoiled_ballots)

    def get_from_ballot_store(
        self, ballot_store: DataStore, build_election_results: BuildElectionResults
    ) -> Tuple[CiphertextTally, List[SubmittedBallot]]:
        self.print_header("Creating Tally")
        ciphertext_tally = TallyStep._get_tally(ballot_store, build_election_results)
        spoiled_ballots = TallyStep._get_spoiled_ballots(ballot_store)
        return (ciphertext_tally, spoiled_ballots)

    @staticmethod
    def _get_tally(
        ballot_store: DataStore, build_election_results: BuildElectionResults
    ) -> CiphertextTally:
        # instead create a CiphertextTally and add all the ballots and remove the ballot_store and ballot_box
        tally = tally_ballots(
            ballot_store,
            build_election_results.internal_manifest,
            build_election_results.context,
        )
        return get_optional(tally)

    @staticmethod
    def _get_spoiled_ballots(ballot_store: DataStore) -> List[SubmittedBallot]:
        submitted_ballots = get_ballots(ballot_store, BallotBoxState.SPOILED)
        spoiled_ballots_list = list(submitted_ballots.values())
        return spoiled_ballots_list
