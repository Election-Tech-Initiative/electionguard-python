from typing import Any
from bson import ObjectId
import eel
from pymongo.database import Database


from electionguard_gui.component_base import ComponentBase
from electionguard_gui.eel_utils import eel_success, utc_to_str
from electionguard_gui.services.key_ceremony_service import KeyCeremonyService


class KeyCeremonyDetailsComponent(ComponentBase):
    """Responsible for retrieving key ceremony details"""

    _key_ceremony_service: KeyCeremonyService

    def __init__(self) -> None:
        super().__init__()
        self._key_ceremony_service = KeyCeremonyService()

    def expose(self) -> None:
        eel.expose(self.get_key_ceremony)
        eel.expose(self.join_key_ceremony)
        eel.expose(self.watch_key_ceremony)
        eel.expose(self.stop_watching_key_ceremony)

    def get_key_ceremony(self, id: str) -> dict[str, Any]:
        db = self.db_service.get_db()
        key_ceremony = get_ceremony(db, id)
        return eel_success(key_ceremony)

    def watch_key_ceremony(self, key_ceremony_id: str) -> None:
        db = self.db_service.get_db()
        print(f"watching key ceremony '{key_ceremony_id}'")
        self._key_ceremony_service.watch_key_ceremonies(
            db, key_ceremony_id, lambda: refresh_ceremony(db, key_ceremony_id)
        )

    def stop_watching_key_ceremony(self) -> None:
        self._key_ceremony_service.stop_watching()

    def join_key_ceremony(self, key_id: str) -> None:
        db = self.db_service.get_db()
        key_ceremony = db.key_ceremonies.find_one({"_id": ObjectId(key_id)})
        key_ceremony["guardians_joined"] += 1
        key_ceremony_name = key_ceremony["key_ceremony_name"]
        guardians_joined = key_ceremony["guardians_joined"]
        db.key_ceremonies.replace_one({"_id": ObjectId(key_id)}, key_ceremony)
        self._key_ceremony_service.notify_changed(db, key_id)
        print(
            f"new guardian joined {key_ceremony_name}, total joined is now {guardians_joined}"
        )


def refresh_ceremony(db: Database, id: str) -> None:
    key_ceremony = get_ceremony(db, id)
    eel.refresh_key_ceremony(key_ceremony)


def get_ceremony(db: Database, id: str) -> dict[str, Any]:
    print(f"getting key ceremony {id}")
    key_ceremony = db.key_ceremonies.find_one({"_id": ObjectId(id)})
    created_at_utc = key_ceremony["created_at"]
    key_ceremony["created_at_str"] = utc_to_str(created_at_utc)
    return key_ceremony
