from typing import Any
from bson import ObjectId
import eel
from pymongo.database import Database

from electionguard_gui.components.component_base import ComponentBase
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
        key_ceremony = self.get_ceremony(db, id)
        key_ceremony["can_join"] = self.can_join_key_ceremony(key_ceremony)
        return eel_success(key_ceremony)

    def can_join_key_ceremony(self, key_ceremony) -> bool:
        user_id = self.auth_service.get_user_id()
        already_joined = user_id in key_ceremony["guardians_joined"]
        is_admin = self.auth_service.is_admin()
        return not already_joined and not is_admin

    def watch_key_ceremony(self, key_ceremony_id: str) -> None:
        db = self.db_service.get_db()
        self.log.debug(f"watching key ceremony '{key_ceremony_id}'")
        self._key_ceremony_service.watch_key_ceremonies(
            db, key_ceremony_id, lambda: self.refresh_ceremony(db, key_ceremony_id)
        )

    def stop_watching_key_ceremony(self) -> None:
        self._key_ceremony_service.stop_watching()

    def join_key_ceremony(self, key_id: str) -> None:
        db = self.db_service.get_db()
        # append the current user's id to the list of guardians
        user_id = self.auth_service.get_user_id()
        db.key_ceremonies.update_one(
            {"_id": ObjectId(key_id)}, {"$push": {"guardians_joined": user_id}}
        )
        self.log.debug(f"adding {user_id} to key ceremony {key_id}")
        self._key_ceremony_service.notify_changed(db, key_id)

    def refresh_ceremony(self, db: Database, id: str) -> None:
        key_ceremony = self.get_ceremony(db, id)
        # pylint: disable=no-member
        eel.refresh_key_ceremony(key_ceremony)

    def get_ceremony(self, db: Database, id: str) -> dict[str, Any]:
        self.log.debug(f"getting key ceremony {id}")
        key_ceremony = db.key_ceremonies.find_one({"_id": ObjectId(id)})
        created_at_utc = key_ceremony["created_at"]
        key_ceremony["created_at_str"] = utc_to_str(created_at_utc)
        return key_ceremony
