from typing import List
from io import TextIOWrapper
from os import listdir
from os.path import join

from electionguard import CiphertextElectionContext
from electionguard.ballot import SubmittedBallot
from electionguard.encrypt import EncryptionDevice
from electionguard.guardian import Guardian, PrivateGuardianRecord
from electionguard.manifest import Manifest
from electionguard.serialize import from_file

from .import_ballot_inputs import (
    ImportBallotInputs,
)
from ..cli_steps import (
    InputRetrievalStepBase,
)


class ImportBallotsInputRetrievalStep(InputRetrievalStepBase):
    """Responsible for retrieving and parsing user provided inputs for the CLI's import ballots command."""

    def get_inputs(
        self,
        manifest_file: TextIOWrapper,
        context_file: TextIOWrapper,
        ballots_dir: str,
        guardian_keys: str,
        encryption_device_file: str,
        output_record: str,
    ) -> ImportBallotInputs:

        self.print_header("Retrieving Inputs")
        manifest: Manifest = self._get_manifest(manifest_file)
        context = InputRetrievalStepBase._get_context(context_file)
        guardians = ImportBallotsInputRetrievalStep._get_guardians_from_keys(
            guardian_keys, context
        )
        encryption_devices = self._get_encryption_devices(encryption_device_file)
        submitted_ballots = ImportBallotsInputRetrievalStep._get_ballots(
            ballots_dir, SubmittedBallot
        )

        self.print_value("Ballots Dir", ballots_dir)

        return ImportBallotInputs(
            guardians,
            manifest,
            submitted_ballots,
            context,
            encryption_devices,
            output_record,
        )

    def _get_encryption_devices(
        self, encryption_device_file: str
    ) -> List[EncryptionDevice]:
        if encryption_device_file is None:
            return []
        encryption_device = from_file(EncryptionDevice, encryption_device_file)
        self.print_value("Encryption device id", encryption_device.device_id)
        self.print_value("Encryption device location", encryption_device.location)
        return [encryption_device]

    @staticmethod
    def _get_guardians_from_keys(
        guardian_keys_dir: str, context: CiphertextElectionContext
    ) -> List[Guardian]:

        files = listdir(guardian_keys_dir)
        private_records = [
            ImportBallotsInputRetrievalStep._load_private_record(guardian_keys_dir, f)
            for f in files
        ]
        return list(
            map(
                lambda record: ImportBallotsInputRetrievalStep._get_guardian(
                    record, context
                ),
                private_records,
            )
        )

    @staticmethod
    def _load_private_record(guardian_dir: str, filename: str) -> PrivateGuardianRecord:
        full_file = join(guardian_dir, filename)
        return from_file(PrivateGuardianRecord, full_file)

    @staticmethod
    def _get_guardian(
        private_record: PrivateGuardianRecord, context: CiphertextElectionContext
    ) -> Guardian:
        return Guardian.from_private_record(
            private_record, context.number_of_guardians, context.quorum
        )
