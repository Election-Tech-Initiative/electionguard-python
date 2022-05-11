from io import TextIOWrapper
from electionguard.ballot import PlaintextBallot

from electionguard.manifest import Manifest

from .encrypt_ballot_inputs import EncryptBallotInputs
from ..cli_steps import (
    InputRetrievalStepBase,
)


class EncryptBallotsInputRetrievalStep(InputRetrievalStepBase):
    """Responsible for retrieving and parsing user provided inputs for the CLI's encrypt ballots command."""

    def get_inputs(
        self,
        manifest_file: TextIOWrapper,
        context_file: TextIOWrapper,
        ballots_dir: str,
    ) -> EncryptBallotInputs:

        self.print_header("Retrieving Inputs")
        manifest: Manifest = self._get_manifest(manifest_file)
        context = InputRetrievalStepBase._get_context(context_file)
        plaintext_ballots = InputRetrievalStepBase._get_ballots(
            ballots_dir, PlaintextBallot
        )

        return EncryptBallotInputs(
            manifest,
            context,
            plaintext_ballots,
        )
