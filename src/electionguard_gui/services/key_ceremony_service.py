from threading import Event
from typing import Any, Callable, List, Optional
from datetime import datetime
from pymongo.database import Database
from pymongo import CursorType
from bson import ObjectId
import eel
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
from electionguard_gui.services.eel_log_service import EelLogService

from electionguard_gui.services.service_base import ServiceBase


class KeyCeremonyService(ServiceBase):
    """Responsible for functionality related to key ceremonies"""

    _log: EelLogService
    _auth_service: AuthorizationService

    def __init__(
        self, log_service: EelLogService, auth_service: AuthorizationService
    ) -> None:
        self._log = log_service
        self._auth_service = auth_service

    MS_TO_BLOCK = 200

    # assumptions: 1. only one thread will be watching key ceremonies at a time, and 2. a class instance will be
    # maintained for the duration of the time watching key ceremonies.  However, both will always be true given
    # how eel works.
    watching_key_ceremonies = Event()

    def watch_key_ceremonies(
        self,
        db: Database,
        key_ceremony_id: Optional[str],
        on_found: Callable[[str], None],
    ) -> None:
        # retrieve a tailable cursor of the deltas in key ceremony to avoid polling
        cursor = db.key_ceremony_deltas.find(
            {}, cursor_type=CursorType.TAILABLE_AWAIT
        ).max_await_time_ms(self.MS_TO_BLOCK)
        # burn through all updates that have occurred up till now so next time we only get new ones
        for _ in cursor:
            pass

        if self.watching_key_ceremonies.is_set():
            self.stop_watching()

        # set a semaphore to indicate that we are watching key ceremonies
        self.watching_key_ceremonies.set()
        while self.watching_key_ceremonies.is_set() and cursor.alive:
            try:
                # block for up to a few seconds until someone adds a new key ceremony delta
                delta = cursor.next()
                changed_id = delta["key_ceremony_id"]
                if key_ceremony_id is None or key_ceremony_id == changed_id:
                    print("new key ceremony delta found")
                    on_found(changed_id)

            except StopIteration:
                # the tailable cursor times out after a few seconds and fires a StopIteration exception,
                # so we need to catch it and restart watching. The sleep is required by eel to allow
                # it to respond to events such as the very important stop_watching event.
                eel.sleep(0.8)

    def stop_watching(self) -> None:
        self.watching_key_ceremonies.clear()

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

    # pylint: disable=no-self-use
    def notify_changed(self, db: Database, key_ceremony_id: str) -> None:
        # notify watchers that the key ceremony was modified
        db.key_ceremony_deltas.insert_one({"key_ceremony_id": key_ceremony_id})

    def get_guardian_number(
        self, key_ceremony: KeyCeremonyDto, guardian_id: str
    ) -> int:
        """Returns the position of a guardian within the array of guardians that have joined
        a key ceremony. This technique is important because it avoids concurrency problems
        that could arise if simply retrieving the number of guardians"""
        guardian_num = 1
        for guardian in key_ceremony.guardians_joined:
            if guardian == guardian_id:
                return guardian_num
            guardian_num += 1
        raise ValueError(f"guardian '{guardian_id}' not found")

    # pylint: disable=no-self-use
    def get(self, db: Database, id: str) -> KeyCeremonyDto:
        key_ceremony_dict = db.key_ceremonies.find_one({"_id": ObjectId(id)})
        if key_ceremony_dict is None:
            raise ValueError(f"key ceremony '{id}' not found")
        return KeyCeremonyDto(key_ceremony_dict)

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
