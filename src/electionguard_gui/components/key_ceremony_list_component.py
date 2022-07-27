import eel
from pymongo.database import Database

from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.services.key_ceremony_service import KeyCeremonyService


class KeyCeremonyListComponent(ComponentBase):
    """Responsible for functionality related to the guardian home page"""

    _key_ceremony_service: KeyCeremonyService

    def __init__(self, key_ceremony_service: KeyCeremonyService) -> None:
        super().__init__()
        self._key_ceremony_service = key_ceremony_service

    def expose(self) -> None:
        eel.expose(self.watch_key_ceremonies)
        eel.expose(self.stop_watching_key_ceremonies)

    def watch_key_ceremonies(self) -> None:
        self._log.debug("Watching key ceremonies")
        db = self._db_service.get_db()
        self.send_key_ceremonies_to_ui(db)
        self._key_ceremony_service.watch_key_ceremonies(
            db, None, lambda _: self.send_key_ceremonies_to_ui(db)
        )
        self._log.debug("exited watching key_ceremonies")

    def stop_watching_key_ceremonies(self) -> None:
        self._log.debug("Stopping watch key_ceremonies")
        self._key_ceremony_service.stop_watching()

    def send_key_ceremonies_to_ui(self, db: Database) -> None:
        key_ceremonies = self._key_ceremony_service.get_active(db)
        js_key_ceremonies = [
            key_ceremony.to_id_name_dict() for key_ceremony in key_ceremonies
        ]
        # pylint: disable=no-member
        eel.key_ceremonies_found(js_key_ceremonies)
