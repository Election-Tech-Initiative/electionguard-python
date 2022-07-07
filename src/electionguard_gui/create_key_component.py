from typing import Any
import eel
from pymongo.results import InsertOneResult

from electionguard_gui.component_base import ComponentBase


class CreateKeyComponent(ComponentBase):
    """Responsible for functionality related to creating keys"""

    def expose(self) -> None:
        eel.expose(self.start_ceremony)

    def start_ceremony(
        self, key_name: str, guardian_count: int, quorum: int
    ) -> dict[str, Any]:
        if guardian_count < quorum:
            return self.eel_fail(
                "Guardian count must be greater than or equal to quorum"
            )

        print(
            f"Starting ceremony: key_name: {key_name}, guardian_count: {guardian_count}, quorum: {quorum}"
        )
        db = self.get_db()
        existing_keys = db.keys.find_one({"key_name": key_name})
        if existing_keys:
            print(f"record '{key_name}' already exists")
            result: dict[str, Any] = self.eel_fail("Key name already exists")
            return result
        key = {
            "key_name": key_name,
            "guardian_count": guardian_count,
            "quorum": quorum,
            "guardians_joined": 0,
        }
        inserted_id = db.keys.insert_one(key).inserted_id
        print(f"created '{key_name}' record, id: {inserted_id}")
        return self.eel_success(inserted_id)
