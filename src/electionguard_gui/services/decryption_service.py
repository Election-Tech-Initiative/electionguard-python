from datetime import datetime
from typing import Any, Dict, List, Optional
from bson import ObjectId
from pymongo.database import Database
from electionguard.decryption_share import DecryptionShare
from electionguard.election_polynomial import LagrangeCoefficientsRecord
from electionguard.key_ceremony import ElectionPublicKey
from electionguard.serialize import to_raw
from electionguard.tally import PlaintextTally, PublishedCiphertextTally
from electionguard.type import BallotId
from electionguard_gui.models.decryption_dto import DecryptionDto
from electionguard_gui.models.election_dto import ElectionDto
from electionguard_gui.services.db_watcher_service import DbWatcherService
from electionguard_gui.services.eel_log_service import EelLogService
from electionguard_gui.services.service_base import ServiceBase
from electionguard_gui.services.authorization_service import AuthorizationService


class DecryptionService(ServiceBase):
    """Responsible for functionality related to decryption operations"""

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
        ballot_count = election.sum_ballots()
        ballot_upload_count = len(election.ballot_uploads)
        decryption: dict[str, Any] = {
            "election_id": election.id,
            "election_name": election.election_name,
            "ballot_count": ballot_count,
            "ballot_upload_count": ballot_upload_count,
            "key_ceremony_id": election.key_ceremony_id,
            "guardians": election.guardians,
            "quorum": election.quorum,
            "decryption_name": decryption_name,
            "guardians_joined": [],
            "decryption_shares": [],
            "plaintext_spoiled_ballots": None,
            "plaintext_tally": None,
            "lagrange_coefficients": None,
            "ciphertext_tally": None,
            "completed_at": None,
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

    def get_active(self, db: Database) -> List[DecryptionDto]:
        self._log.trace("getting all decryptions")
        decryption_cursor = db.decryptions.find(
            {
                "completed_at": None,
            }
        )
        decryption_list = [
            DecryptionDto(decryption) for decryption in decryption_cursor
        ]
        return decryption_list

    def append_guardian_joined(
        self,
        db: Database,
        decryption_id: str,
        guardian_id: str,
        decryption_share: DecryptionShare,
        ballot_shares: Dict[BallotId, Optional[DecryptionShare]],
        guardian_key: ElectionPublicKey,
    ) -> None:
        decryption_share_raw = to_raw(decryption_share)
        self._log.trace(
            f"appending guardian {guardian_id} to decryption {decryption_id}"
        )
        ballot_shares_dict = {
            ballot_id: to_ballot_share_raw(ballot_share)
            for (ballot_id, ballot_share) in ballot_shares.items()
        }
        db.decryptions.update_one(
            {"_id": ObjectId(decryption_id)},
            {
                "$push": {
                    "decryption_shares": {
                        "guardian_id": guardian_id,
                        "guardian_key": to_raw(guardian_key),
                        "decryption_share": decryption_share_raw,
                        "ballot_shares": ballot_shares_dict,
                    }
                }
            },
        )
        db.decryptions.update_one(
            {"_id": ObjectId(decryption_id)},
            {"$push": {"guardians_joined": guardian_id}},
        )

    def set_decryption_completed(
        self,
        db: Database,
        decryption_id: str,
        plaintext_tally: PlaintextTally,
        plaintext_spoiled_ballots: Dict[BallotId, PlaintextTally],
        lagrange_coefficients: LagrangeCoefficientsRecord,
        ciphertext_tally: PublishedCiphertextTally,
    ) -> None:
        self._log.trace("setting decryption completed")

        plaintext_spoiled_ballots_dict = {
            str(ballot_id): to_raw(plaintext_tally)
            for (ballot_id, plaintext_tally) in plaintext_spoiled_ballots.items()
        }

        db.decryptions.update_one(
            {"_id": ObjectId(decryption_id)},
            {
                "$set": {
                    "completed_at": datetime.utcnow(),
                    "plaintext_tally": to_raw(plaintext_tally),
                    "plaintext_spoiled_ballots": plaintext_spoiled_ballots_dict,
                    "lagrange_coefficients": to_raw(lagrange_coefficients),
                    "ciphertext_tally": to_raw(ciphertext_tally),
                }
            },
        )


def to_ballot_share_raw(ballot_share: Optional[DecryptionShare]) -> Optional[str]:
    if ballot_share is None:
        return None
    return to_raw(ballot_share)
