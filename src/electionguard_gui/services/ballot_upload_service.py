from datetime import datetime
from bson import ObjectId
from pymongo.database import Database
from electionguard.ballot import SubmittedBallot
from electionguard.serialize import from_raw
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
        ballot_count: int,
        created_at: datetime,
    ) -> str:
        ballot_upload = {
            "election_id": election_id,
            "device_file_name": device_file_name,
            "device_file_contents": device_file_contents,
            "ballot_count": ballot_count,
            "ballots": [],
            "created_by": self._auth_service.get_user_id(),
            "created_at": created_at,
        }
        self._log.trace(f"inserting ballot upload for: {election_id}")
        inserted_id = db.ballot_uploads.insert_one(ballot_upload).inserted_id
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

    def get_ballots(self, db: Database, election_id: str) -> list[SubmittedBallot]:
        self._log.trace(f"getting ballots for {election_id}")
        ballot_uploads = db.ballot_uploads.find({"election_id": election_id})
        ballots = []
        for ballot_upload in ballot_uploads:
            for ballot_obj in ballot_upload["ballots"]:
                ballot_str = ballot_obj["file_contents"]
                ballot = from_raw(SubmittedBallot, ballot_str)
                ballots.append(ballot)
        return ballots
