from typing import List, Tuple
from electionguard.utils import get_optional
from electionguard.data_store import DataStore
from electionguard.tally import CiphertextTally, tally_ballots
from electionguard.ballot_box import get_ballots
from electionguard.ballot import BallotBoxState, SubmittedBallot

from electionguard_cli.cli_models.e2e_build_election_results import BuildElectionResults
from electionguard_cli.steps.shared.cli_step_base import CliStepBase


class TallyStep(CliStepBase):
    """Responsible for creating a tally and retrieving spoiled ballots."""

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
