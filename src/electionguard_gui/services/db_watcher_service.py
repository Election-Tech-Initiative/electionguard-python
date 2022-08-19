from typing import Callable, Optional
from threading import Event
import eel
from pymongo.database import Database
from pymongo import CursorType
from electionguard_gui.services.eel_log_service import EelLogService
from electionguard_gui.services.service_base import ServiceBase


class DbWatcherService(ServiceBase):
    """
    Responsible for long polling against the database in order to notify clients that
    changes have occurred to data within collections
    """

    _log: EelLogService

    def __init__(self, log_service: EelLogService) -> None:
        self._log = log_service

    MS_TO_BLOCK = 200

    # assumptions: 1. only one thread will be watching the database at a time, and 2. a class instance will be
    # maintained for the duration of the time watching the database.  However, both will always be true given
    # how eel works.
    watching_database = Event()

    def notify_changed(self, db: Database, collection: str, id: str) -> None:
        # notify any watchers that the collection was modified
        self._log.debug(f"notifying watchers of change to {collection} for {id}")
        db.db_deltas.insert_one({"collection": collection, "changed_id": id})

    def watch_database(
        self,
        db: Database,
        id_to_watch: Optional[str],
        on_found: Callable[[str, str], None],
    ) -> None:
        # retrieve a tailable cursor of the deltas in the database to avoid polling
        cursor = db.db_deltas.find(
            {}, cursor_type=CursorType.TAILABLE_AWAIT
        ).max_await_time_ms(self.MS_TO_BLOCK)
        # burn through all updates that have occurred up till now so next time we only get new ones
        for _ in cursor:
            pass

        if self.watching_database.is_set():
            self.stop_watching()

        # set a semaphore to indicate that we are watching the database
        self.watching_database.set()
        while self.watching_database.is_set() and cursor.alive:
            try:
                # block for up to a few seconds until someone adds a new delta
                delta = cursor.next()
                collection = delta["collection"]
                changed_id = delta["changed_id"]
                if id_to_watch is None or id_to_watch == changed_id:
                    self._log.debug(f"new delta found for {collection} {changed_id}")
                    on_found(collection, changed_id)

            except StopIteration:
                # the tailable cursor times out after a few seconds and fires a StopIteration exception,
                # so we need to catch it and restart watching. The sleep is required by eel to allow
                # it to respond to events such as the very important stop_watching event.
                eel.sleep(0.8)

    def stop_watching(self) -> None:
        self.watching_database.clear()
