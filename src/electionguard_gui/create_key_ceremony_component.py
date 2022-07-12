from typing import Any
import eel
from datetime import datetime

from electionguard_gui.component_base import ComponentBase
from electionguard_gui.eel_utils import eel_fail, eel_success


class CreateKeyCeremonyComponent(ComponentBase):
    """Responsible for functionality related to creating key ceremonies"""

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
            "guardians_joined": 0,
            "created_by": self.auth_service.get_user_id(),
            "created_at": datetime.utcnow(),
        }
        inserted_id = db.key_ceremonies.insert_one(key_ceremony).inserted_id
        self.log.debug(f"created '{key_ceremony_name}' record, id: {inserted_id}")
        # notify anyone watching for key ceremony changes that a new key ceremony was created
        db.key_ceremony_deltas.insert_one({"key_ceremony_id": inserted_id})
        return eel_success(str(inserted_id))
