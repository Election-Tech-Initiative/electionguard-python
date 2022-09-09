import os
from tempfile import TemporaryDirectory
from os.path import splitext
from typing import Any
from shutil import make_archive
import eel
from electionguard.constants import get_constants
from electionguard_gui.eel_utils import eel_success
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.services import (
    ElectionService,
    DecryptionService,
    BallotUploadService,
)
from electionguard_gui.services.export_service import get_export_locations
from electionguard_tools.helpers.export import export_record


class ExportElectionRecordComponent(ComponentBase):
    """Responsible for exporting an election record for an election"""

    _COMPRESSION_FORMAT = "zip"

    _election_service: ElectionService
    _decryption_service: DecryptionService
    _ballot_upload_service: BallotUploadService

    def __init__(
        self,
        election_service: ElectionService,
        decryption_service: DecryptionService,
        ballot_upload_service: BallotUploadService,
    ) -> None:
        self._election_service = election_service
        self._decryption_service = decryption_service
        self._ballot_upload_service = ballot_upload_service

    def expose(self) -> None:
        eel.expose(self.export_election_record)
        eel.expose(self.get_election_record_export_locations)

    def get_election_record_export_locations(self) -> dict[str, Any]:
        self._log.trace("getting export locations")
        export_locations = get_export_locations()
        locations = [
            os.path.join(location, "publish-election.zip")
            for location in export_locations
        ]
        return eel_success(locations)

    def export_election_record(
        self, decryption_id: str, location: str
    ) -> dict[str, Any]:
        db = self._db_service.get_db()
        self._log.debug(f"exporting election record {decryption_id} to {location}")
        decryption = self._decryption_service.get(db, decryption_id)
        election = self._election_service.get(db, decryption.election_id)
        context = election.get_context()
        manifest = election.get_manifest()
        constants = get_constants()
        encryption_devices = election.get_encryption_devices()
        submitted_ballots = self._ballot_upload_service.get_ballots(
            db, election.id, lambda x: None
        )
        plaintext_tally = decryption.get_plaintext_tally()
        spoiled_ballots = decryption.get_plaintext_spoiled_ballots()
        lagrange_coefficients = decryption.get_lagrange_coefficients()
        ciphertext_tally = decryption.get_ciphertext_tally()
        guardian_records = election.get_guardian_records()
        with TemporaryDirectory() as temp_dir:
            export_record(
                manifest,
                context,
                constants,
                encryption_devices,
                submitted_ballots,
                spoiled_ballots,
                ciphertext_tally,
                plaintext_tally,
                guardian_records,
                lagrange_coefficients,
                election_record_directory=temp_dir,
            )
            file_name = splitext(location)[0]
            make_archive(file_name, self._COMPRESSION_FORMAT, temp_dir)

        return eel_success()
