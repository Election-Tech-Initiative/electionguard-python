from typing import Any
import eel
from electionguard_gui.eel_utils import eel_success
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.services import KeyCeremonyService


class CreateElectionComponent(ComponentBase):
    """Responsible for functionality related to creating encryption packages for elections"""

    _key_ceremony_service: KeyCeremonyService

    def __init__(self, key_ceremony_service: KeyCeremonyService) -> None:
        self._key_ceremony_service = key_ceremony_service

    def expose(self) -> None:
        eel.expose(self.get_keys)

    def get_keys(self) -> dict[str, Any]:
        self._log.debug("Getting keys")
        db = self._db_service.get_db()
        completed_key_ceremonies = self._key_ceremony_service.get_completed(db)
        keys = [
            key_ceremony.to_id_name_dict() for key_ceremony in completed_key_ceremonies
        ]
        return eel_success(keys)
