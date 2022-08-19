from typing import Optional
from electionguard_tools.factories import BallotFactory

from .cli_step_base import CliStepBase
from ..cli_models import BuildElectionResults, MarkResults


class MarkBallotsStep(CliStepBase):
    """Responsible for marking ballots."""

    def mark(
        self,
        build_election_results: BuildElectionResults,
        num_ballots: int,
        ballot_style_id: Optional[str],
    ) -> MarkResults:
        self.print_header("Marking Ballots")
        internal_manifest = build_election_results.internal_manifest
        ballot_factory = BallotFactory()
        plaintext_ballots = ballot_factory.generate_fake_plaintext_ballots_for_election(
            internal_manifest,
            num_ballots,
            ballot_style_id,
            allow_null_votes=False,
            allow_under_votes=False,
        )
        return MarkResults(plaintext_ballots)
