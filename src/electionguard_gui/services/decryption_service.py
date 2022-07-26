from datetime import datetime
from typing import Any
from bson import ObjectId
from pymongo.database import Database
from electionguard_gui.models.decryption_dto import DecryptionDto
from electionguard_gui.services.eel_log_service import EelLogService
from electionguard_gui.services.service_base import ServiceBase
from electionguard_gui.services.authorization_service import AuthorizationService


class DecryptionService(ServiceBase):
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
        election_name: str,
        decryption_name: str,
    ) -> str:
        election = {
            "election_id": election_id,
            "election_name": election_name,
            "decryption_name": decryption_name,
            "guardians_joined": [],
            "created_by": self._auth_service.get_user_id(),
            "created_at": datetime.utcnow(),
        }
        self._log.trace(f"inserting decryption for: {election_id}")
        inserted_id = db.decryptions.insert_one(election).inserted_id
        return str(inserted_id)

    def name_exists(self, db: Database, name: str) -> Any:
        self._log.trace(f"getting decryption by name: {name}")
        decryption = db.decryptions.find_one({"name": name})
        return decryption is not None

    def get(self, db: Database, decryption_id: str) -> DecryptionDto:
        self._log.trace(f"getting decryption {decryption_id}")
        decryption = db.decryptions.find_one({"_id": ObjectId(decryption_id)})
        return DecryptionDto(decryption)

    def get_decryption_count(self, db: Database, election_id: str) -> int:
        self._log.trace(f"getting decryption count for election {election_id}")
        decryption_count = db.decryptions.count_documents({"election_id": election_id})
        return decryption_count
