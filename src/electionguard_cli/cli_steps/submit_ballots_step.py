from typing import List
import click

from electionguard.data_store import DataStore
from electionguard.ballot_box import BallotBox
from electionguard.ballot import CiphertextBallot

from .cli_step_base import CliStepBase
from ..cli_models import BuildElectionResults, SubmitResults


class SubmitBallotsStep(CliStepBase):
    """Responsible for submitting ballots."""

    def submit(
        self,
        build_election_results: BuildElectionResults,
        cast_ballots: List[CiphertextBallot],
        spoil_ballots: List[CiphertextBallot],
    ) -> SubmitResults:
        self.print_header("Submitting Ballots")
        internal_manifest = build_election_results.internal_manifest
        context = build_election_results.context

        ballot_store: DataStore = DataStore()
        ballot_box = BallotBox(internal_manifest, context, ballot_store)

        for ballot in cast_ballots:
            ballot_box.cast(ballot)
            click.echo(f"Cast Ballot Id: {ballot.object_id}")

        for ballot in spoil_ballots:
            ballot_box.spoil(ballot)
            click.echo(f"Spoilt Ballot Id: {ballot.object_id}")

        return SubmitResults(ballot_store.all())
