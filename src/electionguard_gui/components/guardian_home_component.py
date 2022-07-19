import eel
from pymongo.database import Database

from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.services.key_ceremony_service import KeyCeremonyService


class GuardianHomeComponent(ComponentBase):
    """Responsible for functionality related to the guardian home page"""

    _key_ceremony_service: KeyCeremonyService

    def __init__(self, key_ceremony_service: KeyCeremonyService) -> None:
        super().__init__()
        self._key_ceremony_service = key_ceremony_service

    def expose(self) -> None:
        eel.expose(self.watch_key_ceremonies)
        eel.expose(self.stop_watching_key_ceremonies)

    def watch_key_ceremonies(self) -> None:
        self.log.debug("Watching key ceremonies")
        db = self.db_service.get_db()
        send_key_ceremonies_to_ui(db)
        self._key_ceremony_service.watch_key_ceremonies(
            db, None, lambda: send_key_ceremonies_to_ui(db)
        )
        self.log.debug("exited watching key_ceremonies")

    def stop_watching_key_ceremonies(self) -> None:
        self.log.debug("Stopping watch key_ceremonies")
        self._key_ceremony_service.stop_watching()


def send_key_ceremonies_to_ui(db: Database) -> None:
    key_ceremonies = db.key_ceremonies.find()
    js_key_ceremonies = [
        make_js_key_ceremony(key_ceremony) for key_ceremony in key_ceremonies
    ]
    # pylint: disable=no-member
    eel.key_ceremonies_found(js_key_ceremonies)


def make_js_key_ceremony(key_ceremony: dict) -> dict:
    return {
        "key_ceremony_name": key_ceremony["key_ceremony_name"],
        "id": key_ceremony["_id"].__str__(),
    }
