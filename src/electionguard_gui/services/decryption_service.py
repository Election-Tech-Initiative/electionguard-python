from datetime import datetime
from pymongo.database import Database
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
        name: str,
    ) -> str:
        election = {
            "election_id": election_id,
            "name": name,
            "created_by": self._auth_service.get_user_id(),
            "created_at": datetime.utcnow(),
        }
        self._log.trace(f"inserting decryption for: {election_id}")
        inserted_id = db.decryptions.insert_one(election).inserted_id
        return str(inserted_id)
