from io import TextIOWrapper

from electionguard.manifest import Manifest

from .mark_ballot_inputs import MarkBallotInputs
from ..cli_steps import (
    InputRetrievalStepBase,
)


class MarkBallotsInputRetrievalStep(InputRetrievalStepBase):
    """Responsible for retrieving and parsing user provided inputs for the CLI's mark ballots command."""

    def get_inputs(
        self,
        manifest_file: TextIOWrapper,
        context_file: TextIOWrapper,
    ) -> MarkBallotInputs:

        self.print_header("Retrieving Inputs")
        manifest: Manifest = self._get_manifest(manifest_file)
        context = InputRetrievalStepBase._get_context(context_file)

        return MarkBallotInputs(
            manifest,
            context,
        )
