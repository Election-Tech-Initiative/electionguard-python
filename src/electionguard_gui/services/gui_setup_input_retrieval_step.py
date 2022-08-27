from typing import Optional
from electionguard import Manifest
from electionguard.guardian import Guardian
from electionguard_cli import SetupInputs
from electionguard_cli.setup_election import SetupInputRetrievalStep


class GuiSetupInputRetrievalStep(SetupInputRetrievalStep):
    """Responsible for retrieving and parsing user provided inputs for the GUI's setup election command."""

    def get_gui_inputs(
        self,
        guardian_count: int,
        quorum: int,
        guardians: list[Guardian],
        verification_url: Optional[str],
        manifest_raw: str,
    ) -> SetupInputs:

        self.print_header("Retrieving Inputs")
        manifest: Manifest = self._get_manifest_raw(manifest_raw)
        return SetupInputs(
            guardian_count, quorum, guardians, manifest, verification_url, force=True
        )
