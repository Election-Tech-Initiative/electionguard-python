from typing import List
import click

from electionguard.data_store import DataStore
from electionguard.ballot_box import BallotBox
from electionguard.election import CiphertextElectionContext
from electionguard.manifest import InternalManifest
from electionguard.utils import get_optional
from electionguard.ballot import (
    CiphertextBallot,
)

from ..cli_models import BuildElectionResults, EncryptResults
from ..cli_steps import CliStepBase
from .e2e_inputs import E2eInputs


class SubmitVotesStep(CliStepBase):
    """Responsible for submitting ballots into a ballot store."""

    def submit(
        self,
        e2e_inputs: E2eInputs,
        build_election_results: BuildElectionResults,
        e2e_encrypt_results: EncryptResults,
    ) -> DataStore:
        self.print_header("Submitting Ballots")
        internal_manifest = build_election_results.internal_manifest
        context = build_election_results.context
        ballot_store = SubmitVotesStep._cast_and_spoil(
            internal_manifest,
            context,
            e2e_encrypt_results.ciphertext_ballots,
            e2e_inputs,
        )
        return ballot_store

    @staticmethod
    def _cast_and_spoil(
        internal_manifest: InternalManifest,
        context: CiphertextElectionContext,
        ciphertext_ballots: List[CiphertextBallot],
        e2e_inputs: E2eInputs,
    ) -> DataStore:
        ballot_store: DataStore = DataStore()
        ballot_box = BallotBox(internal_manifest, context, ballot_store)

        for ballot in ciphertext_ballots:
            spoil = ballot.object_id == e2e_inputs.spoil_id
            if spoil:
                submitted_ballot = ballot_box.spoil(ballot)
            else:
                submitted_ballot = ballot_box.cast(ballot)

            click.echo(
                f"Submitted Ballot Id: {ballot.object_id} state: {get_optional(submitted_ballot).state}"
            )
        return ballot_store
