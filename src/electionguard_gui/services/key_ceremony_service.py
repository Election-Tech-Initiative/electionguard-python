from typing import Any, List
from datetime import datetime
from pymongo.database import Database
from bson import ObjectId
from electionguard.key_ceremony import (
    ElectionJointKey,
    ElectionPartialKeyBackup,
    ElectionPartialKeyVerification,
    ElectionPublicKey,
)
from electionguard_gui.models.key_ceremony_dto import KeyCeremonyDto
from electionguard_gui.services.authorization_service import AuthorizationService
from electionguard_gui.services.db_serialization_service import (
    backup_to_dict,
    joint_key_to_dict,
    public_key_to_dict,
    verification_to_dict,
)
from electionguard_gui.services.db_watcher_service import DbWatcherService
from electionguard_gui.services.eel_log_service import EelLogService

from electionguard_gui.services.service_base import ServiceBase


class KeyCeremonyService(ServiceBase):
    """Responsible for functionality related to key ceremonies"""

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
        self, db: Database, key_ceremony_name: str, guardian_count: int, quorum: int
    ) -> str:
        key_ceremony = {
            "key_ceremony_name": key_ceremony_name,
            "guardian_count": guardian_count,
            "quorum": quorum,
            "guardians_joined": [],
            "keys": [],
            "guardians_keys": [],
            "other_keys": [],
            "backups": [],
            "shared_backups": [],
            "verifications": [],
            "joint_key": None,
            "created_by": self._auth_service.get_user_id(),
            "created_at": datetime.utcnow(),
            "completed_at": None,
        }
        inserted_id = db.key_ceremonies.insert_one(key_ceremony).inserted_id
        self._log.debug(f"created '{key_ceremony_name}' record, id: {inserted_id}")
        return str(inserted_id)

    def notify_changed(self, db: Database, key_ceremony_id: str) -> None:
        self._db_watcher_service.notify_changed(db, "key_ceremonies", key_ceremony_id)

    # pylint: disable=no-self-use
    def get(self, db: Database, id: str) -> KeyCeremonyDto:
        key_ceremony_dict = db.key_ceremonies.find_one({"_id": ObjectId(id)})
        if key_ceremony_dict is None:
            raise ValueError(f"key ceremony '{id}' not found")
        dto = KeyCeremonyDto(key_ceremony_dict)
        dto.set_can_join(self._auth_service)
        return dto

    def append_guardian_joined(
        self, db: Database, key_ceremony_id: str, guardian_id: str
    ) -> None:
        db.key_ceremonies.update_one(
            {"_id": ObjectId(key_ceremony_id)},
            {"$push": {"guardians_joined": guardian_id}},
        )

    def append_key(
        self, db: Database, key_ceremony_id: str, key: ElectionPublicKey
    ) -> None:
        db.key_ceremonies.update_one(
            {"_id": ObjectId(key_ceremony_id)},
            {"$push": {"keys": public_key_to_dict(key)}},
        )

    def append_other_key(self, db: Database, key_ceremony_id: str, keys: Any) -> None:
        db.key_ceremonies.update_one(
            {"_id": ObjectId(key_ceremony_id)},
            {"$push": {"other_keys": {"$each": keys}}},
        )

    def append_backups(
        self,
        db: Database,
        key_ceremony_id: str,
        backups: List[ElectionPartialKeyBackup],
    ) -> None:
        backups_dict = [backup_to_dict(backup) for backup in backups]
        db.key_ceremonies.update_one(
            {"_id": ObjectId(key_ceremony_id)},
            {"$push": {"backups": {"$each": backups_dict}}},
        )

    def append_shared_backups(
        self,
        db: Database,
        key_ceremony_id: str,
        shared_backups: List[Any],
    ) -> None:
        db.key_ceremonies.update_one(
            {"_id": ObjectId(key_ceremony_id)},
            {"$push": {"shared_backups": {"$each": shared_backups}}},
        )

    def append_verifications(
        self,
        db: Database,
        key_ceremony_id: str,
        verifications: List[ElectionPartialKeyVerification],
    ) -> None:
        verifications_dict = [
            verification_to_dict(verification) for verification in verifications
        ]
        db.key_ceremonies.update_one(
            {"_id": ObjectId(key_ceremony_id)},
            {"$push": {"verifications": {"$each": verifications_dict}}},
        )

    def append_joint_key(
        self,
        db: Database,
        key_ceremony_id: str,
        joint_key: ElectionJointKey,
    ) -> None:
        joint_key_dict = joint_key_to_dict(joint_key)
        db.key_ceremonies.update_one(
            {"_id": ObjectId(key_ceremony_id)},
            {"$set": {"joint_key": joint_key_dict}},
        )

    def set_complete(
        self,
        db: Database,
        key_ceremony_id: str,
    ) -> None:
        db.key_ceremonies.update_one(
            {"_id": ObjectId(key_ceremony_id)},
            {"$set": {"completed_at": datetime.utcnow()}},
        )

    def get_completed(self, db: Database) -> List[KeyCeremonyDto]:
        key_ceremonies = db.key_ceremonies.find({"completed_at": {"$ne": None}})
        return [KeyCeremonyDto(key_ceremony) for key_ceremony in key_ceremonies]

    def get_active(self, db: Database) -> List[KeyCeremonyDto]:
        key_ceremonies = db.key_ceremonies.find({"completed_at": {"$eq": None}})
        return [KeyCeremonyDto(key_ceremony) for key_ceremony in key_ceremonies]

    def exists(self, db: Database, key_ceremony_name: str) -> bool:
        existing_key_ceremonies = db.key_ceremonies.find_one(
            {"key_ceremony_name": key_ceremony_name}
        )
        return existing_key_ceremonies is not None


def get_guardian_number(key_ceremony: KeyCeremonyDto, guardian_id: str) -> int:
    """Returns the position of a guardian within the array of guardians that have joined
    a key ceremony. This technique is important because it avoids concurrency problems
    that could arise if simply retrieving the number of guardians"""
    guardian_num = 1
    for guardian in key_ceremony.guardians_joined:
        if guardian == guardian_id:
            return guardian_num
        guardian_num += 1
    raise ValueError(f"guardian '{guardian_id}' not found")
