from typing import Any
from datetime import datetime
import eel
from electionguard_gui.components.component_base import ComponentBase

from electionguard_gui.eel_utils import eel_fail, eel_success
from electionguard_gui.services.authorization_service import AuthoriationService
from electionguard_gui.services.key_ceremony_service import KeyCeremonyService


class CreateKeyCeremonyComponent(ComponentBase):
    """Responsible for functionality related to creating key ceremonies"""

    _key_ceremony_service: KeyCeremonyService
    _auth_service: AuthoriationService

    def __init__(
        self,
        key_ceremony_service: KeyCeremonyService,
        auth_service: AuthoriationService,
    ) -> None:
        super().__init__()
        self._key_ceremony_service = key_ceremony_service
        self._auth_service = auth_service

    def expose(self) -> None:
        eel.expose(self.create_key_ceremony)

    def create_key_ceremony(
        self, key_ceremony_name: str, guardian_count: int, quorum: int
    ) -> dict[str, Any]:
        if guardian_count < quorum:
            return eel_fail("Guardian count must be greater than or equal to quorum")

        self.log.debug(
            "Starting ceremony: "
            + f"key_ceremony_name: {key_ceremony_name}, "
            + f"guardian_count: {guardian_count}, "
            + f"quorum: {quorum}"
        )
        db = self.db_service.get_db()
        existing_key_ceremonies = db.key_ceremonies.find_one(
            {"key_ceremony_name": key_ceremony_name}
        )
        if existing_key_ceremonies:
            self.log.debug(f"record '{key_ceremony_name}' already exists")
            result: dict[str, Any] = eel_fail("Key ceremony name already exists")
            return result
        key_ceremony = {
            "key_ceremony_name": key_ceremony_name,
            "guardian_count": guardian_count,
            "quorum": quorum,
            "guardians_joined": [],
            "guardians_keys": [],
            "created_by": self._auth_service.get_user_id(),
            "created_at": datetime.utcnow(),
        }
        inserted_id = db.key_ceremonies.insert_one(key_ceremony).inserted_id
        self.log.debug(f"created '{key_ceremony_name}' record, id: {inserted_id}")
        self._key_ceremony_service.notify_changed(db, inserted_id)
        return eel_success(str(inserted_id))
