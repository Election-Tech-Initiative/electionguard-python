from threading import Event
from bson import ObjectId
from pymongo import CursorType
import eel

from electionguard_gui.component_base import ComponentBase


class GuardianHomeComponent(ComponentBase):
    """Responsible for functionality related to the guardian home page"""

    MS_TO_BLOCK = 2000
    watching_key_ceremonies = Event()

    def expose(self) -> None:
        eel.expose(self.watch_key_ceremonies)
        eel.expose(self.stop_watching)
        eel.expose(self.join_key_ceremony)

    def watch_key_ceremonies(self) -> None:
        db = self.db_service.get_db()

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
                _ = cursor.next()
                print("new key ceremony delta found, refreshing key ceremonies in UI")
                key_ceremonies = db.key_ceremonies.find()
                js_key_ceremonies = [
                    make_js_key_ceremony(key_ceremony)
                    for key_ceremony in key_ceremonies
                ]
                # pylint: disable=no-member
                eel.key_ceremonies_found(js_key_ceremonies)

            except StopIteration:
                # the tailable cursor times out after a few seconds and fires a StopIteration exception,
                # so we need to catch it and restart watching. The sleep is required by eel to allow
                # watching_key_ceremonies to get set in  order to get a clean exit.
                eel.sleep(0.1)

        print("exited watch key_ceremonies loop")

    def stop_watching(self) -> None:
        print("stop_watching")
        self.watching_key_ceremonies.clear()

    def join_key_ceremony(self, key_id: str) -> None:
        db = self.db_service.get_db()
        key_ceremony = db.key_ceremonies.find_one({"_id": ObjectId(key_id)})
        key_ceremony["guardians_joined"] += 1
        key_ceremony_name = key_ceremony["key_ceremony_name"]
        guardians_joined = key_ceremony["guardians_joined"]
        db.key_ceremonies.replace_one({"_id": ObjectId(key_id)}, key_ceremony)
        print(
            f"new guardian joined {key_ceremony_name}, total joined is now {guardians_joined}"
        )


def make_js_key_ceremony(key_ceremony: dict) -> dict:
    return {
        "key_ceremony_name": key_ceremony["key_ceremony_name"],
        "id": key_ceremony["_id"].__str__(),
    }
