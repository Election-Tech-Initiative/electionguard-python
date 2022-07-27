from datetime import datetime
from bson import ObjectId
from pymongo.database import Database
from electionguard_gui.services.eel_log_service import EelLogService
from electionguard_gui.services.service_base import ServiceBase
from electionguard_gui.services.authorization_service import AuthorizationService


class BallotUploadService(ServiceBase):
    """Responsible for functionality related to ballot uploads"""

    _log: EelLogService
    _auth_service: AuthorizationService

    def __init__(
        self, log_service: EelLogService, auth_service: AuthorizationService
    ) -> None:
        self._log = log_service
        self._auth_service = auth_service

    def create(
        self,
        db: Database,
        election_id: str,
        device_file_name: str,
        device_file_contents: str,
    ) -> str:
        election = {
            "election_id": election_id,
            "device_file_name": device_file_name,
            "device_file_contents": device_file_contents,
            "ballots": [],
            "created_by": self._auth_service.get_user_id(),
            "created_at": datetime.utcnow(),
        }
        self._log.trace(f"inserting ballot upload for: {election_id}")
        inserted_id = db.ballot_uploads.insert_one(election).inserted_id
        return str(inserted_id)

    def add_ballot(
        self,
        db: Database,
        ballot_upload_id: str,
        file_name: str,
        file_contents: str,
    ) -> None:
        self._log.trace(f"adding ballot {file_name} to {ballot_upload_id}")
        db.ballot_uploads.update_one(
            {"_id": ObjectId(ballot_upload_id)},
            {
                "$push": {
                    "ballots": {"file_name": file_name, "file_contents": file_contents}
                }
            },
        )
