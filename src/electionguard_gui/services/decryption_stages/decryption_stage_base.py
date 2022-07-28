from abc import ABC
from pymongo.database import Database
from electionguard_gui.models.decryption_dto import DecryptionDto

from electionguard_gui.services.authorization_service import AuthorizationService
from electionguard_gui.services.ballot_upload_service import BallotUploadService
from electionguard_gui.services.db_service import DbService
from electionguard_gui.services.decryption_service import DecryptionService
from electionguard_gui.services.eel_log_service import EelLogService
from electionguard_gui.services.election_service import ElectionService
from electionguard_gui.services.guardian_service import GuardianService


class DecryptionStageBase(ABC):
    """Responsible for shared functionality across all decryption stages"""

    _log: EelLogService
    _db_service: DbService
    _decryption_service: DecryptionService
    _auth_service: AuthorizationService
    _guardian_service: GuardianService
    _election_service: ElectionService
    _ballot_upload_service: BallotUploadService

    def __init__(
        self,
        log_service: EelLogService,
        db_service: DbService,
        decryption_service: DecryptionService,
        auth_service: AuthorizationService,
        guardian_service: GuardianService,
        election_service: ElectionService,
        ballot_upload_service: BallotUploadService,
    ):
        self._db_service = db_service
        self._decryption_service = decryption_service
        self._auth_service = auth_service
        self._log = log_service
        self._guardian_service = guardian_service
        self._election_service = election_service
        self._ballot_upload_service = ballot_upload_service

    def run(self, db: Database, decryption: DecryptionDto) -> None:
        pass
