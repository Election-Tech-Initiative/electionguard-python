import traceback
from typing import Any
import eel
from pymongo.database import Database
from electionguard_gui.eel_utils import eel_fail, eel_success
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.models.decryption_dto import DecryptionDto
from electionguard_gui.services import (
    ElectionService,
    DecryptionService,
    DbWatcherService,
)
from electionguard_gui.services.decryption_stages import (
    DecryptionS1JoinService,
    DecryptionS2AnnounceService,
)


class ViewDecryptionComponent(ComponentBase):
    """Responsible for functionality related to creating decryptions for an election"""

    _decryption_service: DecryptionService
    _election_service: ElectionService
    _decryption_s1_join_service: DecryptionS1JoinService
    _decryption_s2_announce_service: DecryptionS2AnnounceService
    _db_watcher_service: DbWatcherService

    def __init__(
        self,
        decryption_service: DecryptionService,
        election_service: ElectionService,
        decryption_s1_join_service: DecryptionS1JoinService,
        decryption_s2_announce_service: DecryptionS2AnnounceService,
        db_watcher_service: DbWatcherService,
    ) -> None:
        self._decryption_service = decryption_service
        self._election_service = election_service
        self._decryption_s1_join_service = decryption_s1_join_service
        self._decryption_s2_announce_service = decryption_s2_announce_service
        self._db_watcher_service = db_watcher_service

    def expose(self) -> None:
        eel.expose(self.get_decryption)
        eel.expose(self.watch_decryption)
        eel.expose(self.stop_watching_decryption)
        eel.expose(self.join_decryption)

    def watch_decryption(self, decryption_id: str) -> None:
        try:
            db = self._db_service.get_db()
            self._log.debug(f"watching decryption '{decryption_id}'")
            self._db_watcher_service.watch_database(
                db, decryption_id, self.on_decryption_changed
            )
        except Exception as e:  # pylint: disable=broad-except
            self.handle_error(e)
            self._db_watcher_service.stop_watching()
            # no need to raise exception or return anything, we're in fire-and-forget mode here

    def stop_watching_decryption(self) -> None:
        self._db_watcher_service.stop_watching()

    def on_decryption_changed(self, _: str, decryption_id: str) -> None:
        try:
            self._log.debug(f"on_key_ceremony_changed decryption_id: '{decryption_id}'")

            db = self._db_service.get_db()
            decryption = self._decryption_service.get(db, decryption_id)
            self.try_run_stage_2(db, decryption)
            refresh_decryption(eel_success())
        # pylint: disable=broad-except
        except Exception as e:
            self._log.error("error in on decryption changed", e)
            traceback.print_exc()
            refresh_decryption(eel_fail(str(e)))

    def try_run_stage_2(self, db: Database, decryption: DecryptionDto) -> bool:
        if self._decryption_s2_announce_service.should_run(db, decryption):
            refresh_decryption(eel_success())
            # give the UI a chance to update
            eel.sleep(0.5)
            self._decryption_s2_announce_service.run(db, decryption)
            return True
        return False

    def get_decryption(self, decryption_id: str, is_refresh: bool) -> dict[str, Any]:
        try:
            db = self._db_service.get_db()
            decryption = self._decryption_service.get(db, decryption_id)
            if not is_refresh:
                did_run = self.try_run_stage_2(db, decryption)
                if did_run:
                    decryption = self._decryption_service.get(db, decryption_id)
            return eel_success(decryption.to_dict())
        # pylint: disable=broad-except
        except Exception as e:
            return self.handle_error(e)

    def join_decryption(self, decryption_id: str) -> dict[str, Any]:
        try:
            db = self._db_service.get_db()
            decryption = self._decryption_service.get(db, decryption_id)
            self._decryption_s1_join_service.run(db, decryption)
            return eel_success(decryption.to_dict())
        # pylint: disable=broad-except
        except Exception as e:
            return self.handle_error(e)


def refresh_decryption(result: dict[str, Any]) -> None:
    # pylint: disable=no-member
    eel.refresh_decryption(result)
