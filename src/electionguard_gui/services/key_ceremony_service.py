from threading import Event
from typing import Any, Callable, Optional
from pymongo.database import Database
from pymongo import CursorType
from bson import ObjectId
import eel
from electionguard.key_ceremony import ElectionPublicKey
from electionguard_gui.services.db_service import DbService

from electionguard_gui.services.service_base import ServiceBase


class KeyCeremonyService(ServiceBase):
    """Responsible for functionality related to key ceremonies"""

    db_service: DbService

    def __init__(self, db_service: DbService) -> None:
        super().__init__()
        self.db_service = db_service

    MS_TO_BLOCK = 500

    # assumptions: 1. only one thread will be watching key ceremonies at a time, and 2. a class instance will be
    # maintained for the duration of the time watching key ceremonies.  However, both will always be true given
    # how eel works.
    watching_key_ceremonies = Event()

    def watch_key_ceremonies(
        self,
        db: Database,
        key_ceremony_id: Optional[str],
        on_found: Callable,
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
                    on_found()

            except StopIteration:
                # the tailable cursor times out after a few seconds and fires a StopIteration exception,
                # so we need to catch it and restart watching. The sleep is required by eel to allow
                # it to respond to events such as the very important stop_watching event.
                eel.sleep(0.2)

    def stop_watching(self) -> None:
        self.watching_key_ceremonies.clear()

    # pylint: disable=no-self-use
    def notify_changed(self, db: Database, key_ceremony_id: str) -> None:
        # notify watchers that the key ceremony was modified
        db.key_ceremony_deltas.insert_one({"key_ceremony_id": key_ceremony_id})

    def get_guardian_number(self, key_ceremony: Any, guardian_id: str) -> int:
        """Returns the position of a guardian within the array of guardians that have joined
        a key ceremony. This technique is important because it avoids concurrency problems
        that could arise if simply retrieving the number of guardians"""
        guardian_num = 1
        for guardian in key_ceremony["guardians_joined"]:
            if guardian == guardian_id:
                return guardian_num
            guardian_num += 1
        raise ValueError("guardian not found")

    # pylint: disable=no-self-use
    def get(self, db: Database, id: str) -> Any:
        return db.key_ceremonies.find_one({"_id": ObjectId(id)})

    def join_key_ceremony(
        self, db: Database, key_ceremony_id: str, guardian_id: str
    ) -> None:
        db.key_ceremonies.update_one(
            {"_id": ObjectId(key_ceremony_id)},
            {"$push": {"guardians_joined": guardian_id}},
        )

    def add_key(
        self, db: Database, key_ceremony_id: str, key: ElectionPublicKey
    ) -> None:
        db.key_ceremonies.update_one(
            {"_id": ObjectId(key_ceremony_id)},
            {
                "$push": {
                    "keys": {
                        "owner_id": key.owner_id,
                        "sequence_order": key.sequence_order,
                        "key": str(key.key),
                        "coefficient_commitments": [
                            str(c) for c in key.coefficient_commitments
                        ],
                        "coefficient_proofs": [
                            {
                                "public_key": str(cp.public_key),
                                "commitment": str(cp.commitment),
                                "challenge": str(cp.challenge),
                                "response": str(cp.response),
                                "usage": str(cp.usage),
                            }
                            for cp in key.coefficient_proofs
                        ],
                    }
                }
            },
        )
