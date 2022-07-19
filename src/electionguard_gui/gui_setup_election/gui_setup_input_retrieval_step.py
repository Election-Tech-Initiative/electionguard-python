from typing import Optional
from electionguard import Manifest
from electionguard.key_ceremony import CeremonyDetails
from electionguard_cli import SetupInputs
from electionguard_cli.setup_election import SetupInputRetrievalStep
from electionguard_tools import KeyCeremonyOrchestrator


class GuiSetupInputRetrievalStep(SetupInputRetrievalStep):
    """Responsible for retrieving and parsing user provided inputs for the GUI's setup election command."""

    def get_gui_inputs(
        self,
        guardian_count: int,
        quorum: int,
        verification_url: Optional[str],
        manifest_raw: str,
    ) -> SetupInputs:

        self.print_header("Retrieving Inputs")
        guardians = KeyCeremonyOrchestrator.create_guardians(
            CeremonyDetails(guardian_count, quorum)
        )
        manifest: Manifest = self._get_manifest_raw(manifest_raw)
        return SetupInputs(
            guardian_count, quorum, guardians, manifest, verification_url
        )
