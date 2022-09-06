import os
from typing import Any
from datetime import datetime
import eel
from electionguard.encrypt import EncryptionDevice
from electionguard.serialize import from_file, from_raw
from electionguard.ballot import SubmittedBallot
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.eel_utils import eel_fail, eel_success
from electionguard_gui.services import ElectionService, BallotUploadService
from electionguard_gui.services.export_service import get_removable_drives


class UploadBallotsComponent(ComponentBase):
    """Responsible for uploading ballots to an election via the GUI"""

    _election_service: ElectionService
    _ballot_upload_service: BallotUploadService

    def __init__(
        self,
        election_service: ElectionService,
        ballot_upload_service: BallotUploadService,
    ) -> None:
        self._election_service = election_service
        self._ballot_upload_service = ballot_upload_service

    def expose(self) -> None:
        eel.expose(self.create_ballot_upload)
        eel.expose(self.upload_ballot)
        eel.expose(self.is_wizard_supported)
        eel.expose(self.scan_drives)
        eel.expose(self.upload_ballots)

    def create_ballot_upload(
        self,
        election_id: str,
        device_file_name: str,
        device_file_contents: str,
    ) -> dict[str, Any]:
        try:
            db = self._db_service.get_db()
            self._log.debug(f"creating upload for {election_id}")
            election = self._election_service.get(db, election_id)
            if election is None:
                return eel_fail(f"Election {election_id} not found")
            created_at = datetime.utcnow()
            ballot_upload_id = self._ballot_upload_service.create(
                db,
                election_id,
                device_file_name,
                device_file_contents,
                created_at,
            )
            self._election_service.append_ballot_upload(
                db,
                election_id,
                ballot_upload_id,
                device_file_contents,
                created_at,
            )
            return eel_success(ballot_upload_id)
        # pylint: disable=broad-except
        except Exception as e:
            return self.handle_error(e)

    def upload_ballot(
        self,
        ballot_upload_id: str,
        election_id: str,
        file_name: str,
        file_contents: str,
    ) -> dict[str, Any]:
        try:
            db = self._db_service.get_db()
            self._log.trace(f"adding ballot {file_name} to {ballot_upload_id}")
            ballot = from_raw(SubmittedBallot, file_contents)
            election = self._election_service.get(db, election_id)
            context = election.get_context()
            if context.manifest_hash != ballot.manifest_hash:
                self._log.warn(
                    f"ballot '{ballot.object_id}' had a mismatched manifest hash. "
                    + f"Expected {context.manifest_hash}, got {ballot.manifest_hash}."
                )
                return eel_fail(
                    "The uploaded ballot didn't match the encryption package for this election. "
                    + "Please try a different ballot."
                )
            is_duplicate = self._ballot_upload_service.any_ballot_exists(
                db, election_id, ballot.object_id
            )
            if is_duplicate:
                self._log.warn(
                    "ballot '{ballot.object_id}' already exists in election '{election_id}'"
                )
                return eel_success({"is_duplicate": True})

            success = self._ballot_upload_service.add_ballot(
                db,
                ballot_upload_id,
                election_id,
                file_name,
                file_contents,
                ballot.object_id,
            )
            if success:
                self._ballot_upload_service.increment_ballot_count(db, ballot_upload_id)
                self._election_service.increment_ballot_upload_ballot_count(
                    db, election_id, ballot_upload_id
                )
            return eel_success({"is_duplicate": False})
        # pylint: disable=broad-except
        except Exception as e:
            return self.handle_error(e)

    # pylint: disable=no-self-use
    def is_wizard_supported(self) -> bool:
        on_windows = os.name == "nt"
        return on_windows

    def scan_drives(self) -> dict[str, Any]:
        try:
            removable_drives = get_removable_drives()
            self._log.trace(f"found {len(removable_drives)} removable drives")
            candidate_drives = [
                self.parse_drive(drive)
                for drive in removable_drives
                if os.path.exists(os.path.join(drive, "artifacts", "encrypted_ballots"))
                and os.path.exists(os.path.join(drive, "artifacts", "devices"))
            ]
            first_candidate = next(iter(candidate_drives), None)
            return eel_success(first_candidate)
        # pylint: disable=broad-except
        except Exception as e:
            return self.handle_error(e)

    def parse_drive(self, drive: str) -> dict[str, Any]:
        ballots_dir = os.path.join(drive, "artifacts", "encrypted_ballots")
        devices_dir = os.path.join(drive, "artifacts", "devices")
        device_files = os.listdir(devices_dir)
        device_file_name = next(iter(os.listdir(devices_dir)))
        device_file_path = os.path.join(devices_dir, device_file_name)
        if len(device_files) > 1:
            self._log.warn(
                "found multiple device files in drive, using " + device_file_name
            )
        device_file_json = from_file(EncryptionDevice, device_file_path)
        location = device_file_json.location
        ballot_count = len(os.listdir(ballots_dir))
        return {
            "drive": drive,
            "ballots": ballot_count,
            "location": location,
            "device_file_name": device_file_name,
            "device_file_path": device_file_path,
            "ballots_dir": ballots_dir,
        }

    def upload_ballots(self, election_id: str) -> dict[str, Any]:
        try:
            update_upload_status("Scanning drives")
            drive_info = self.scan_drives()
            device_file_name = drive_info["result"]["device_file_name"]
            device_file_path = drive_info["result"]["device_file_path"]
            self._log.debug(
                f"uploading ballots for {election_id} from {device_file_path} device {device_file_name}"
            )
            update_upload_status("Uploading device file")
            ballot_upload_result = self.create_ballot_upload_from_file(
                election_id,
                device_file_name,
                device_file_path,
            )
            if not ballot_upload_result["success"]:
                return ballot_upload_result

            ballots_dir: str = drive_info["result"]["ballots_dir"]
            ballot_files = os.listdir(ballots_dir)
            ballot_upload_id: str = ballot_upload_result["result"]
            ballot_num = 1
            duplicate_count = 0
            ballot_count = len(ballot_files)
            for ballot_file in ballot_files:
                self._log.debug("uploading ballot " + ballot_file)
                update_upload_status(f"Uploading ballot {ballot_num}/{ballot_count}")
                result = self.create_ballot_from_file(
                    election_id, ballot_file, ballot_upload_id, ballots_dir
                )
                if not result["success"]:
                    return result
                if result["result"]["is_duplicate"]:
                    duplicate_count += 1
                ballot_num += 1
            return eel_success(
                {"ballot_count": ballot_count, "duplicate_count": duplicate_count}
            )
        # pylint: disable=broad-except
        except Exception as e:
            return self.handle_error(e)

    def create_ballot_from_file(
        self,
        election_id: str,
        ballot_file_name: str,
        ballot_upload_id: str,
        ballots_dir: str,
    ) -> dict[str, Any]:
        ballot_file_path = os.path.join(ballots_dir, ballot_file_name)
        with open(ballot_file_path, "r", encoding="utf-8") as ballot_file:
            ballot_contents = ballot_file.read()
            return self.upload_ballot(
                ballot_upload_id, election_id, ballot_file_name, ballot_contents
            )

    def create_ballot_upload_from_file(
        self, election_id: str, device_file_name: str, device_file_path: str
    ) -> dict[str, Any]:
        with open(device_file_path, "r", encoding="utf-8") as device_file:
            ballot_upload = self.create_ballot_upload(
                election_id, device_file_name, device_file.read()
            )
            return ballot_upload


def update_upload_status(status: str) -> None:
    # pylint: disable=no-member
    eel.update_upload_status(status)
