from typing import List

from electionguard.election import CiphertextElectionContext
from electionguard.manifest import Manifest
from electionguard.ballot import CiphertextBallot

from ..cli_models import (
    CliElectionInputsBase,
)


class SubmitBallotInputs(CliElectionInputsBase):
    """Responsible for holding the inputs for the CLI's submit ballots command"""

    def __init__(
        self,
        manifest: Manifest,
        context: CiphertextElectionContext,
        cast_ballots: List[CiphertextBallot],
        spoil_ballots: List[CiphertextBallot],
    ):
        self.guardian_count = context.number_of_guardians
        self.quorum = context.quorum
        self.manifest = manifest
        self.context = context
        self.cast_ballots = cast_ballots
        self.spoil_ballots = spoil_ballots

    context: CiphertextElectionContext
