from typing import Any
import eel
from electionguard_gui.eel_utils import eel_success

from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.services.key_ceremony_service import KeyCeremonyService


class KeyCeremonyListComponent(ComponentBase):
    """Responsible for functionality related to the guardian home page"""

    _key_ceremony_service: KeyCeremonyService

    def __init__(self, key_ceremony_service: KeyCeremonyService) -> None:
        super().__init__()
        self._key_ceremony_service = key_ceremony_service

    def expose(self) -> None:
        eel.expose(self.get_key_ceremonies)
        eel.expose(self.watch_key_ceremonies)
        eel.expose(self.stop_watching_key_ceremonies)

    def get_key_ceremonies(self) -> dict[str, Any]:
        db = self._db_service.get_db()
        key_ceremonies = self._key_ceremony_service.get_active(db)
        js_key_ceremonies = [
            key_ceremony.to_id_name_dict() for key_ceremony in key_ceremonies
        ]
        return eel_success(js_key_ceremonies)

    def watch_key_ceremonies(self) -> None:
        self._log.debug("Watching key ceremonies")
        db = self._db_service.get_db()
        self._key_ceremony_service.watch_key_ceremonies(
            db, None, self.notify_ui_key_ceremonies_changed
        )
        self._log.debug("exited watching key_ceremonies")

    def stop_watching_key_ceremonies(self) -> None:
        self._log.debug("Stopping watch key_ceremonies")
        self._key_ceremony_service.stop_watching()

    def notify_ui_key_ceremonies_changed(self, _) -> None:
        # pylint: disable=no-member
        eel.key_ceremonies_changed()
