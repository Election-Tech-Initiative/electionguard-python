from io import TextIOWrapper
from typing import Optional
from electionguard.key_ceremony import CeremonyDetails
from electionguard.manifest import Manifest
from electionguard_tools.helpers.key_ceremony_orchestrator import (
    KeyCeremonyOrchestrator,
)

from .setup_inputs import SetupInputs
from ..cli_steps import InputRetrievalStepBase


class SetupInputRetrievalStep(InputRetrievalStepBase):
    """Responsible for retrieving and parsing user provided inputs for the CLI's setup election command."""

    def get_inputs(
        self,
        guardian_count: int,
        quorum: int,
        manifest_file: TextIOWrapper,
        verification_url: Optional[str],
    ) -> SetupInputs:

        self.print_header("Retrieving Inputs")
        guardians = KeyCeremonyOrchestrator.create_guardians(
            CeremonyDetails(guardian_count, quorum)
        )
        manifest: Manifest = self._get_manifest(manifest_file)

        return SetupInputs(
            guardian_count, quorum, guardians, manifest, verification_url
        )
