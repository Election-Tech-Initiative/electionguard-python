from electionguard.election import CiphertextElectionContext
from electionguard.manifest import Manifest

from ..cli_models import (
    CliElectionInputsBase,
)


class MarkBallotInputs(CliElectionInputsBase):
    """Responsible for holding the inputs for the CLI's mark ballots command"""

    def __init__(
        self,
        manifest: Manifest,
        context: CiphertextElectionContext,
    ):
        self.guardian_count = context.number_of_guardians
        self.quorum = context.quorum
        self.manifest = manifest
        self.context = context

    context: CiphertextElectionContext
