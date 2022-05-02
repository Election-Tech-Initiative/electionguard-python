from typing import List
from electionguard.ballot import SubmittedBallot
from electionguard.election import CiphertextElectionContext
from electionguard.encrypt import EncryptionDevice
from electionguard.guardian import Guardian
from electionguard.manifest import Manifest

from ..cli_models import (
    CliElectionInputsBase,
)


# pylint: disable=too-many-instance-attributes
class ImportBallotInputs(CliElectionInputsBase):
    """Responsible for holding the inputs for the CLI's import ballots command"""

    def __init__(
        self,
        guardians: List[Guardian],
        manifest: Manifest,
        submitted_ballots: List[SubmittedBallot],
        context: CiphertextElectionContext,
        encryption_device: List[EncryptionDevice],
        output_record: str,
    ):
        self.guardian_count = context.number_of_guardians
        self.quorum = context.quorum
        self.guardians = guardians
        self.manifest = manifest
        self.submitted_ballots = submitted_ballots
        self.context = context
        self.encryption_devices = encryption_device
        self.output_record = output_record

    submitted_ballots: List[SubmittedBallot]
    context: CiphertextElectionContext
    encryption_devices: List[EncryptionDevice]
    output_record: str
