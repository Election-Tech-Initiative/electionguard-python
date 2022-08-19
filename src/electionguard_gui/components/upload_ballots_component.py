from typing import Any
from datetime import datetime
import eel
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.eel_utils import eel_fail, eel_success
from electionguard_gui.services import ElectionService, BallotUploadService


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

    def create_ballot_upload(
        self,
        election_id: str,
        device_file_name: str,
        device_file_contents: str,
        ballot_count: int,
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
                ballot_count,
                created_at,
            )
            self._election_service.append_ballot_upload(
                db,
                election_id,
                ballot_upload_id,
                device_file_contents,
                ballot_count,
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
            self._log.debug(f"adding ballot {file_name} to {ballot_upload_id}")
            self._ballot_upload_service.add_ballot(
                db, ballot_upload_id, election_id, file_name, file_contents
            )
            return eel_success()
        # pylint: disable=broad-except
        except Exception as e:
            return self.handle_error(e)
