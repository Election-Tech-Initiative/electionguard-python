from threading import Event
from typing import Callable, Optional
from pymongo.database import Database
from pymongo import CursorType
import eel

from electionguard_gui.services.service_base import ServiceBase


class KeyCeremonyService(ServiceBase):
    """Responsible for functionality related to key ceremonies"""

    MS_TO_BLOCK = 500

    # assumptions: 1. only one thread will be watching key ceremonies at a time, and 2. a class instance will be
    # maintained for the duration of the time watching key ceremonies.  However, both will always be true given
    # how eel works.
    watching_key_ceremonies = Event()

    def watch_key_ceremonies(
        self,
        db: Database,
        key_ceremony_id: Optional[str],
        on_found: Callable,
    ) -> None:
        # retrieve a tailable cursor of the deltas in key ceremony to avoid polling
        cursor = db.key_ceremony_deltas.find(
            {}, cursor_type=CursorType.TAILABLE_AWAIT
        ).max_await_time_ms(self.MS_TO_BLOCK)
        # burn through all updates that have occurred up till now so next time we only get new ones
        for _ in cursor:
            pass

        if self.watching_key_ceremonies.is_set():
            self.stop_watching()

        # set a semaphore to indicate that we are watching key ceremonies
        self.watching_key_ceremonies.set()
        while self.watching_key_ceremonies.is_set() and cursor.alive:
            try:
                # block for up to a few seconds until someone adds a new key ceremony delta
                delta = cursor.next()
                changed_id = delta["key_ceremony_id"]
                if key_ceremony_id is None or key_ceremony_id == changed_id:
                    print("new key ceremony delta found")
                    on_found()

            except StopIteration:
                # the tailable cursor times out after a few seconds and fires a StopIteration exception,
                # so we need to catch it and restart watching. The sleep is required by eel to allow
                # it to respond to events such as the very important stop_watching event.
                eel.sleep(0.2)

    def stop_watching(self) -> None:
        self.watching_key_ceremonies.clear()

    # pylint: disable=no-self-use
    def notify_changed(self, db: Database, key_ceremony_id: str) -> None:
        # notify watchers that the key ceremony was modified
        db.key_ceremony_deltas.insert_one({"key_ceremony_id": key_ceremony_id})
