from typing import List

from electionguard.guardian import Guardian
from electionguard.manifest import Manifest

from ..cli_models import CliElectionInputsBase


class SetupInputs(CliElectionInputsBase):
    """Responsible for holding the inputs for the CLI's setup election command."""

    def __init__(
        self,
        guardian_count: int,
        quorum: int,
        guardians: List[Guardian],
        manifest: Manifest,
        out: str,
        zip: bool,
    ):
        self.guardian_count = guardian_count
        self.quorum = quorum
        self.guardians = guardians
        self.manifest = manifest
        self.out = out
        self.zip = zip

    out: str
