from typing import List
from electionguard.ballot import PlaintextBallot, SubmittedBallot
from electionguard.election import CiphertextElectionContext
from electionguard.encrypt import EncryptionDevice
from electionguard.manifest import Manifest

from ..cli_models import (
    CliElectionInputsBase,
)


class EncryptBallotInputs(CliElectionInputsBase):
    """Responsible for holding the inputs for the CLI's encrypt ballots command"""

    def __init__(
        self,
        manifest: Manifest,
        context: CiphertextElectionContext,
        plaintext_ballots: List[PlaintextBallot],
    ):
        self.manifest = manifest
        self.plaintext_ballots = plaintext_ballots
        self.context = context

    plaintext_ballots: List[SubmittedBallot]
    context: CiphertextElectionContext
    encryption_devices: List[EncryptionDevice]
    output_record: str
