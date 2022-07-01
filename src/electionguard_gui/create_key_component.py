from typing import Any
from time import sleep
import eel

from electionguard_gui.component_base import ComponentBase


class CreateKeyComponent(ComponentBase):
    """Responsible for functionality related to creating keys"""

    def expose(self) -> None:
        eel.expose(self.start_ceremony)

    def start_ceremony(
        self, key_name: str, guardian_count: int, quorum: int
    ) -> dict[str, Any]:
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
        print(f"creating '{key_name}' record")
        db.keys.insert_one(key)
        # todo: poll until guardians accept key
        sleep(1)
        return self.eel_success()
