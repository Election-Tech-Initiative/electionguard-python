from typing import Any
import eel

from electionguard_gui.component_base import ComponentBase


class CreateKeyCeremonyComponent(ComponentBase):
    """Responsible for functionality related to creating key ceremonies"""

    def expose(self) -> None:
        eel.expose(self.create_key_ceremony)

    def create_key_ceremony(
        self, key_ceremony_name: str, guardian_count: int, quorum: int
    ) -> dict[str, Any]:
        if guardian_count < quorum:
            return self.eel_fail(
                "Guardian count must be greater than or equal to quorum"
            )

        print(
            f"Starting ceremony: key_ceremony_name: {key_ceremony_name}, guardian_count: {guardian_count}, quorum: {quorum}"
        )
        db = self.db_service.get_db()
        existing_key_ceremonies = db.key_ceremonies.find_one(
            {"key_ceremony_name": key_ceremony_name}
        )
        if existing_key_ceremonies:
            print(f"record '{key_ceremony_name}' already exists")
            result: dict[str, Any] = self.eel_fail("Key ceremony name already exists")
            return result
        key_ceremony = {
            "key_ceremony_name": key_ceremony_name,
            "guardian_count": guardian_count,
            "quorum": quorum,
            "guardians_joined": 0,
        }
        inserted_id = db.key_ceremonies.insert_one(key_ceremony).inserted_id
        print(f"created '{key_ceremony_name}' record, id: {inserted_id}")
        return self.eel_success(inserted_id)
