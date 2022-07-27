from datetime import datetime
from typing import Any, List
from bson import ObjectId
from pymongo.database import Database
from electionguard_gui.models.decryption_dto import DecryptionDto
from electionguard_gui.models.election_dto import ElectionDto
from electionguard_gui.services.db_watcher_service import DbWatcherService
from electionguard_gui.services.eel_log_service import EelLogService
from electionguard_gui.services.service_base import ServiceBase
from electionguard_gui.services.authorization_service import AuthorizationService


class DecryptionService(ServiceBase):
    """Responsible for functionality related to ballot uploads"""

    _log: EelLogService
    _auth_service: AuthorizationService
    _db_watcher_service: DbWatcherService

    def __init__(
        self,
        log_service: EelLogService,
        auth_service: AuthorizationService,
        db_watcher_service: DbWatcherService,
    ) -> None:
        self._log = log_service
        self._auth_service = auth_service
        self._db_watcher_service = db_watcher_service

    def create(
        self,
        db: Database,
        election: ElectionDto,
        decryption_name: str,
    ) -> str:
        decryption = {
            "election_id": election.id,
            "election_name": election.election_name,
            "guardians": election.guardians,
            "quorum": election.quorum,
            "decryption_name": decryption_name,
            "guardians_joined": [],
            "created_by": self._auth_service.get_user_id(),
            "created_at": datetime.utcnow(),
        }
        self._log.trace(f"inserting decryption for: {election.id}")
        insert_result = db.decryptions.insert_one(decryption)
        inserted_id = str(insert_result.inserted_id)
        self.notify_changed(db, inserted_id)
        return inserted_id

    def notify_changed(self, db: Database, decryption_id: str) -> None:
        self._db_watcher_service.notify_changed(db, "decryptions", decryption_id)

    def name_exists(self, db: Database, name: str) -> Any:
        self._log.trace(f"getting decryption by name: {name}")
        decryption = db.decryptions.find_one({"decryption_name": name})
        return decryption is not None

    def get(self, db: Database, decryption_id: str) -> DecryptionDto:
        self._log.trace(f"getting decryption {decryption_id}")
        decryption = db.decryptions.find_one({"_id": ObjectId(decryption_id)})
        if decryption is None:
            raise Exception(f"decryption {decryption_id} not found")
        dto = DecryptionDto(decryption)
        dto.set_can_join(self._auth_service)
        return dto

    def get_decryption_count(self, db: Database, election_id: str) -> int:
        self._log.trace(f"getting decryption count for election {election_id}")
        decryption_count: int = db.decryptions.count_documents(
            {"election_id": election_id}
        )
        return decryption_count

    def get_all(self, db: Database) -> List[DecryptionDto]:
        self._log.trace("getting all decryptions")
        decryption_cursor = db.decryptions.find()
        decryption_list = [
            DecryptionDto(decryption) for decryption in decryption_cursor
        ]
        return decryption_list
