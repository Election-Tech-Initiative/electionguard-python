from threading import Event
from bson import ObjectId
import eel

from electionguard_gui.component_base import ComponentBase


class GuardianHomeComponent(ComponentBase):
    """Responsible for functionality related to the guardian home page"""

    watching_key_ceremonies = Event()

    def expose(self) -> None:
        eel.expose(self.watch_key_ceremonies)
        eel.expose(self.stop_watching)
        eel.expose(self.join_key_ceremony)

    def watch_key_ceremonies(self) -> None:
        db = self.db_service.get_db()
        last_count = 0
        self.watching_key_ceremonies.set()
        while self.watching_key_ceremonies.is_set():
            current_count = db.key_ceremonies.count_documents({})
            print(f"polling, guardian count = {current_count}")
            if current_count != last_count:
                print(
                    f"found new key ceremony. Count was {last_count}, and is now {current_count}"
                )
                key_ceremonies = db.key_ceremonies.find()
                js_key_ceremonies = [
                    {
                        "key_ceremony_name": key_ceremony["key_ceremony_name"],
                        "id": key_ceremony["_id"].__str__(),
                    }
                    for key_ceremony in key_ceremonies
                ]
                # pylint: disable=no-member
                eel.key_ceremonies_found(js_key_ceremonies)
                print("called key_ceremonies_found successfully")
            last_count = current_count
            eel.sleep(1)
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
