from io import TextIOWrapper

from electionguard.manifest import Manifest

from .setup_inputs import SetupInputs
from ..cli_steps import InputRetrievalStepBase


class SetupInputRetrievalStep(InputRetrievalStepBase):
    """Responsible for retrieving and parsing user provided inputs for the CLI's setup election command."""

    def get_inputs(
        self, guardian_count: int, quorum: int, manifest_file: TextIOWrapper, out: str
    ) -> SetupInputs:

        self.print_header("Retrieving Inputs")
        guardians = InputRetrievalStepBase._get_guardians(guardian_count, quorum)
        manifest: Manifest = self._get_manifest(manifest_file)

        return SetupInputs(guardian_count, quorum, guardians, manifest, out)
