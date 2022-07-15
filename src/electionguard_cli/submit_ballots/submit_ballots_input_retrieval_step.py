from io import TextIOWrapper

from electionguard.manifest import Manifest
from electionguard.ballot import CiphertextBallot

from .submit_ballot_inputs import SubmitBallotInputs
from ..cli_steps import (
    InputRetrievalStepBase,
)


class SubmitBallotsInputRetrievalStep(InputRetrievalStepBase):
    """Responsible for retrieving and parsing user provided inputs for the CLI's submit ballots command."""

    def get_inputs(
        self,
        manifest_file: TextIOWrapper,
        context_file: TextIOWrapper,
        cast_ballots_dir: str,
        spoil_ballots_dir: str,
    ) -> SubmitBallotInputs:

        self.print_header("Retrieving Inputs")
        manifest: Manifest = self._get_manifest(manifest_file)
        context = InputRetrievalStepBase._get_context(context_file)
        cast_ballots = self._get_ballots(cast_ballots_dir, CiphertextBallot)

        if spoil_ballots_dir is not None:
            spoil_ballots = self._get_ballots(spoil_ballots_dir, CiphertextBallot)
        else:
            spoil_ballots = []

        return SubmitBallotInputs(
            manifest,
            context,
            cast_ballots,
            spoil_ballots,
        )
