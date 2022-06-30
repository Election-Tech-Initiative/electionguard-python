from threading import Event
from bson import ObjectId
import eel

from electionguard_gui.component_base import ComponentBase


class GuardianHomeComponent(ComponentBase):
    """Responsible for functionality related to the guardian home page"""

    watching_keys = Event()

    def expose(self) -> None:
        eel.expose(self.watch_keys)
        eel.expose(self.stop_watching)
        eel.expose(self.join_key)

    def watch_keys(self) -> None:
        db = self.get_db()
        last_count = 0
        self.watching_keys.set()
        while self.watching_keys.is_set():
            current_count = db.keys.count_documents({})
            print(f"polling, guardian count = {current_count}")
            if current_count != last_count:
                print(
                    f"found new keys. Count was {last_count}, and is now {current_count}"
                )
                keys = db.keys.find()
                js_keys = [
                    {
                        "key_name": key["key_name"],
                        "id": key["_id"].__str__(),
                    }
                    for key in keys
                ]
                eel.keys_found(js_keys)
                print("called keys_found successfully")
            last_count = current_count
            eel.sleep(1.0)
        print("exited watch keys loop")

    def stop_watching(self) -> None:
        print("stop_watching")
        self.watching_keys.clear()

    def join_key(self, key_id: str) -> None:
        db = self.get_db()
        keys_collection = db.keys
        key = keys_collection.find_one({"_id": ObjectId(key_id)})
        key_name = key["key_name"]
        print(f"gonna join key {key_name}")
