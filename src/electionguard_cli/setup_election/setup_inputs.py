from typing import List, Optional

from electionguard.guardian import Guardian
from electionguard.manifest import Manifest

from ..cli_models import CliElectionInputsBase


class SetupInputs(CliElectionInputsBase):
    """Responsible for holding the inputs for the CLI's setup election command."""

    verification_url: Optional[str]
    force: bool

    def __init__(
        self,
        guardian_count: int,
        quorum: int,
        guardians: List[Guardian],
        manifest: Manifest,
        verification_url: Optional[str],
        force: bool = False,
    ):
        self.guardian_count = guardian_count
        self.quorum = quorum
        self.guardians = guardians
        self.manifest = manifest
        self.verification_url = verification_url
        self.force = force
