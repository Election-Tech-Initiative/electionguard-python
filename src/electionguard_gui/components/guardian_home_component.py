from typing import Any
import eel
from electionguard_gui.eel_utils import eel_success

from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.services import (
    KeyCeremonyService,
    DecryptionService,
    DbWatcherService,
)


class GuardianHomeComponent(ComponentBase):
    """Responsible for functionality related to the guardian home page"""

    _key_ceremony_service: KeyCeremonyService
    _decryption_service: DecryptionService
    _db_watcher_service: DbWatcherService

    def __init__(
        self,
        key_ceremony_service: KeyCeremonyService,
        decryption_service: DecryptionService,
        db_watcher_service: DbWatcherService,
    ) -> None:
        super().__init__()
        self._key_ceremony_service = key_ceremony_service
        self._decryption_service = decryption_service
        self._db_watcher_service = db_watcher_service

    def expose(self) -> None:
        eel.expose(self.get_decryptions)
        eel.expose(self.get_key_ceremonies)
        eel.expose(self.watch_db_collections)
        eel.expose(self.stop_watching_db_collections)

    def get_decryptions(self) -> dict[str, Any]:
        db = self._db_service.get_db()
        decryptions = self._decryption_service.get_active(db)
        decryptions_json = [decryption.to_id_name_dict() for decryption in decryptions]
        return eel_success(decryptions_json)

    def get_key_ceremonies(self) -> dict[str, Any]:
        db = self._db_service.get_db()
        key_ceremonies = self._key_ceremony_service.get_active(db)
        js_key_ceremonies = [
            key_ceremony.to_id_name_dict() for key_ceremony in key_ceremonies
        ]
        return eel_success(js_key_ceremonies)

    def watch_db_collections(self) -> None:
        try:
            self._log.debug("Watching database")
            db = self._db_service.get_db()
            self._db_watcher_service.watch_database(db, None, notify_ui_db_changed)
            self._log.debug("exited watching database")
        except KeyboardInterrupt:
            self._log.debug("Keyboard interrupt, exiting watch database")
            self._db_watcher_service.stop_watching()
        except Exception as e:  # pylint: disable=broad-except
            self.handle_error(e)
            self._db_watcher_service.stop_watching()
            # no need to raise exception or return anything, we're in fire-and-forget mode here

    def stop_watching_db_collections(self) -> None:
        self._log.debug("Stopping watch database")
        self._db_watcher_service.stop_watching()


def notify_ui_db_changed(collection: str, _: str) -> None:
    # pylint: disable=no-member
    if collection == "key_ceremonies":
        eel.key_ceremonies_changed()
    if collection == "decryptions":
        eel.decryptions_changed()
