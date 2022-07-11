from threading import Event
from typing import Callable
from pymongo.database import Database
from pymongo import CursorType
import eel

from electionguard_gui.services.service_base import ServiceBase


class KeyCeremonyService(ServiceBase):
    """Responsible for functionality related to key ceremonies"""

    MS_TO_BLOCK = 1000
    watching_key_ceremonies = Event()

    def watch_key_ceremonies(
        self, db: Database, on_found: Callable[[str], None]
    ) -> None:
        # retrieve a tailable cursor of the deltas in key ceremony to avoid polling
        cursor = db.key_ceremony_deltas.find(
            {}, cursor_type=CursorType.TAILABLE_AWAIT
        ).max_await_time_ms(self.MS_TO_BLOCK)
        # burn through all updates that have occurred up till now so next time we only get new ones
        for _ in cursor:
            pass

        # set a semaphore to indicate that we are watching key ceremonies
        self.watching_key_ceremonies.set()
        while self.watching_key_ceremonies.is_set() and cursor.alive:
            try:
                # block for up to a few seconds until someone adds a new key ceremony delta
                id = cursor.next()
                print("new key ceremony delta found, refreshing key ceremonies in UI")
                on_found(id)

            except StopIteration:
                # the tailable cursor times out after a few seconds and fires a StopIteration exception,
                # so we need to catch it and restart watching. The sleep is required by eel to allow
                # watching_key_ceremonies to get set in  order to get a clean exit.
                eel.sleep(0.1)

    def stop_watching(self) -> None:
        print("stop_watching")
        self.watching_key_ceremonies.clear()
