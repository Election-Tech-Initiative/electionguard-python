from datetime import datetime
from time import sleep
from typing import Callable
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
        created_at: datetime,
    ) -> str:
        ballot_upload = {
            "election_id": election_id,
            "device_file_name": device_file_name,
            "device_file_contents": device_file_contents,
            "ballot_count": 0,
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
        election_id: str,
        file_name: str,
        file_contents: str,
        ballot_object_id: str,
    ) -> bool:
        self._log.trace(f"adding ballot {file_name} to {ballot_upload_id}")
        db.ballot_uploads.insert_one(
            {
                "ballot_upload_id": ballot_upload_id,
                "election_id": election_id,
                "file_name": file_name,
                "object_id": ballot_object_id,
                "file_contents": file_contents,
            }
        )
        return True

    def increment_ballot_count(self, db: Database, ballot_upload_id: str) -> None:
        self._log.trace(f"incrementing ballot count for {ballot_upload_id}")
        db.ballot_uploads.update_one(
            {"_id": ballot_upload_id, "ballot_count": {"$exists": True}},
            {"$inc": {"ballot_count": 1}},
        )

    def any_ballot_exists(self, db: Database, election_id: str, object_id: str) -> bool:
        self._log.trace("checking if ballot exists for {election_id}")
        return (
            db.ballot_uploads.count_documents(
                {"election_id": election_id, "object_id": object_id}
            )
            > 0
        )

    def get_ballots(
        self, db: Database, election_id: str, report_status: Callable[[str], None]
    ) -> list[SubmittedBallot]:
        self._log.debug(f"getting ballots for {election_id}")
        ballot_uploads = list(
            db.ballot_uploads.find(
                {"election_id": election_id, "file_contents": {"$exists": True}},
                projection={"_id": 1, "file_contents": 0},
            )
        )
        ballots = []
        total_ballots = len(ballot_uploads)
        ballot_num = 1
        for ballot_id_obj in ballot_uploads:
            ballot_id = ballot_id_obj["_id"]
            report_status(f"Loading ballot {ballot_num}/{total_ballots}")
            try:
                ballot = self.get_submitted_ballot_with_retry(db, ballot_id)
                ballots.append(ballot)
            # pylint: disable=broad-except
            except Exception as e:
                self._log.error(
                    f"Error deserializing ballot {ballot_id}. "
                    + "Skipping ballot, but this may cause Chaum Pederson errors later.",
                    e,
                )
                # per RC 8/15/22 log errors and continue processing even if it makes numbers incorrect
            ballot_num += 1
        return ballots

    def get_submitted_ballot_with_retry(
        self, db: Database, ballot_upload_id: str
    ) -> SubmittedBallot:
        retry_num = 0
        max_retries = 3
        while retry_num < max_retries:
            try:
                return self.get_submitted_ballot(db, ballot_upload_id)
            except RetryException:
                self._log.warn(
                    f"retrying get ballot {ballot_upload_id} in {retry_num + 1} second(s). Retry #{retry_num + 1}"
                )
                # wait 1 second before retrying in case network was slow
                sleep(retry_num + 1)
            retry_num += 1
        raise Exception(
            f"Failed to get ballot {ballot_upload_id} after {max_retries} retries"
        )

    def get_submitted_ballot(
        self, db: Database, ballot_upload_id: str
    ) -> SubmittedBallot:
        self._log.trace(f"getting submitted ballot {ballot_upload_id}")
        ballot_obj = None
        try:
            ballot_obj = db.ballot_uploads.find_one(
                {"_id": ballot_upload_id}, projection={"file_contents": 1}
            )
        except Exception as e:
            self._log.error(f"mongo error getting ballot {ballot_upload_id}", e)
            raise RetryException from e
        if ballot_obj is None:
            raise Exception(f"Ballot {ballot_upload_id} not found")
        ballot_str = ballot_obj["file_contents"]
        # if ballot_str ends with a }
        if not ballot_str[-1] == "}":
            self._log.warn(f"ballot {ballot_upload_id} is missing a closing bracket")
            raise RetryException
        try:
            ballot = from_raw(SubmittedBallot, ballot_str)
        except Exception as e:
            self._log.error(f"error deserializing ballot {ballot_upload_id}", e)
            raise RetryException from e
        return ballot


class RetryException(Exception):
    """An exception to notify the caller to retry"""
