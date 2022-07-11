from typing import Any
from bson import ObjectId
import eel

from electionguard_gui.component_base import ComponentBase
from electionguard_gui.eel_utils import eel_success


class KeyCeremonyDetailsComponent(ComponentBase):
    """Responsible for retrieving key ceremony details"""

    def expose(self) -> None:
        eel.expose(self.get_key_ceremony)

    def get_key_ceremony(self, id: str) -> dict[str, Any]:
        db = self.db_service.get_db()
        key_ceremony = db.key_ceremonies.find_one({"_id": ObjectId(id)})
        return eel_success(key_ceremony)
