from os import getcwd, path
from typing import Any, List
import eel
from pymongo.database import Database

from electionguard import to_file
from electionguard.guardian import Guardian, PrivateGuardianRecord
from electionguard.key_ceremony import CeremonyDetails
from electionguard.key_ceremony_mediator import KeyCeremonyMediator
from electionguard.serialize import from_file
from electionguard.utils import get_optional
from electionguard_gui.services.db_serialization_service import (
    dict_to_election_public_key,
)
from electionguard_tools.helpers.export import GUARDIAN_PREFIX

from electionguard_gui.services.authorization_service import AuthoriationService
from electionguard_gui.services.guardian_service import make_guardian
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.eel_utils import utc_to_str
from electionguard_gui.services.key_ceremony_service import (
    KeyCeremonyService,
    get_key_ceremony_status,
)


class KeyCeremonyDetailsComponent(ComponentBase):
    """Responsible for retrieving key ceremony details"""

    auth_service: AuthoriationService

    def __init__(
        self,
        key_ceremony_service: KeyCeremonyService,
        auth_service: AuthoriationService,
    ) -> None:
        super().__init__()
        self._key_ceremony_service = key_ceremony_service
        self.auth_service = auth_service

    def expose(self) -> None:
        eel.expose(self.join_key_ceremony)
        eel.expose(self.watch_key_ceremony)
        eel.expose(self.stop_watching_key_ceremony)

    def can_join_key_ceremony(self, key_ceremony) -> bool:
        user_id = self.auth_service.get_user_id()
        already_joined = user_id in key_ceremony["guardians_joined"]
        is_admin = self.auth_service.is_admin()
        return not already_joined and not is_admin

    def watch_key_ceremony(self, key_ceremony_id: str) -> None:
        db = self.db_service.get_db()
        # retrieve and send the key ceremony to the client
        self.on_key_ceremony_changed(key_ceremony_id)
        self.log.debug(f"watching key ceremony '{key_ceremony_id}'")
        # start watching for key ceremony changes from guardians
        self._key_ceremony_service.watch_key_ceremonies(
            db, key_ceremony_id, self.on_key_ceremony_changed
        )

    def on_key_ceremony_changed(self, key_ceremony_id: str) -> None:
        current_user_id = self.auth_service.get_user_id()
        self.log.debug(
            f"on_key_ceremony_changed key_ceremony_id: '{key_ceremony_id}', current_user_id: '{current_user_id}'"
        )
        is_admin = self.auth_service.is_admin()
        is_guardian = not is_admin
        db = self.db_service.get_db()
        key_ceremony = self.get_ceremony(db, key_ceremony_id)
        guardians_joined_count = len(key_ceremony["guardians_joined"])
        guardian_count = key_ceremony["guardian_count"]
        self.log.info(
            f"{guardians_joined_count}/{guardian_count} guardians joined {key_ceremony_id}"
        )
        all_guardians_joined = guardians_joined_count >= guardian_count
        other_keys_exist = len(key_ceremony["other_keys"]) > 0
        if is_admin and all_guardians_joined and not other_keys_exist:
            self.log.info("all guardians have joined, announcing guardians")
            other_keys = self.announce(key_ceremony)
            self.log.debug("saving other_keys")
            self._key_ceremony_service.append_other_key(db, key_ceremony_id, other_keys)
            # this notify_changed occurs inside watch_key_ceremonies and thus may
            #       produce an unnecessary UI refresh for the admin
            self._key_ceremony_service.notify_changed(db, key_ceremony_id)
            # todo #689 wait until all guardians have backups

        # todo: search backups to determine if current user has created backup
        current_user_backup_exists = False
        if is_guardian and other_keys_exist and not current_user_backup_exists:
            self.log.debug("other keys found, creating backup")
            guardian = self.load_guardian(current_user_id, key_ceremony)
            self.log.debug("guardian loaded")

            current_user_other_keys = self.find_other_keys_for_user(
                key_ceremony, current_user_id
            )
            for other_key in current_user_other_keys["other_keys"]:
                other_user = other_key["owner_id"]
                self.log.debug(
                    f"saving other_key from {other_user} for {current_user_id}"
                )
                public_key = dict_to_election_public_key(other_key)
                guardian.save_guardian_key(public_key)
            guardian.generate_election_partial_key_backups()
            backups = guardian.share_election_partial_key_backups()
            self._key_ceremony_service.append_backups(db, key_ceremony_id, backups)

        key_ceremony["status"] = get_key_ceremony_status(key_ceremony)
        # pylint: disable=no-member
        eel.refresh_key_ceremony(key_ceremony)

    def find_other_keys_for_user(self, key_ceremony, user_id) -> Any:
        return next(
            filter(
                lambda other_key: other_key["owner_id"] == user_id,
                key_ceremony["other_keys"],
            )
        )

    def announce(self, key_ceremony: Any) -> List[dict[str, Any]]:
        other_keys = []
        quorum = key_ceremony["quorum"]
        guardian_count = key_ceremony["guardian_count"]
        ceremony_details = CeremonyDetails(guardian_count, quorum)
        mediator: KeyCeremonyMediator = KeyCeremonyMediator(
            "mediator_1", ceremony_details
        )
        guardians = key_ceremony["guardians_joined"]
        for guardian_id in guardians:
            key = find_key(key_ceremony, guardian_id)
            guardian_public_key = dict_to_election_public_key(key)
            mediator.announce(guardian_public_key)
        for guardian_id in guardians:
            other_guardian_keys = get_optional(
                mediator.share_announced(str(guardian_id))
            )
            other_keys.append(
                {
                    "owner_id": guardian_id,
                    "other_keys": [
                        self._key_ceremony_service.public_key_to_dict(key)
                        for key in other_guardian_keys
                    ],
                }
            )
        return other_keys

    def stop_watching_key_ceremony(self) -> None:
        self._key_ceremony_service.stop_watching()

    def join_key_ceremony(self, key_ceremony_id: str) -> None:
        db = self.db_service.get_db()

        # append the current user's id to the list of guardians
        user_id = self.auth_service.get_user_id()
        self._key_ceremony_service.append_guardian_joined(db, key_ceremony_id, user_id)
        key_ceremony = self._key_ceremony_service.get(db, key_ceremony_id)
        guardian_number = self._key_ceremony_service.get_guardian_number(
            key_ceremony, user_id
        )
        self.log.debug(
            f"user {user_id} about to join key ceremony {key_ceremony_id} as guardian #{guardian_number}"
        )
        guardian = make_guardian(user_id, guardian_number, key_ceremony)
        self.save_guardian(guardian, key_ceremony)
        public_key = guardian.share_key()
        self._key_ceremony_service.append_key(db, key_ceremony_id, public_key)
        self.log.debug(
            f"{user_id} joined key ceremony {key_ceremony_id} as guardian #{guardian_number}"
        )
        self._key_ceremony_service.notify_changed(db, key_ceremony_id)

    def load_guardian(self, guardian_id: str, key_ceremony: Any) -> Guardian:
        file_name = GUARDIAN_PREFIX + guardian_id + ".json"
        key_ceremony_id = str(key_ceremony["_id"])
        file_path = path.join(getcwd(), "gui_private_keys", key_ceremony_id, file_name)
        private_guardian_record = from_file(PrivateGuardianRecord, file_path)
        return Guardian.from_private_record(
            private_guardian_record,
            key_ceremony["guardian_count"],
            key_ceremony["quorum"],
        )

    def save_guardian(self, guardian: Guardian, key_ceremony: Any) -> None:
        private_guardian_record = guardian.export_private_data()
        file_name = GUARDIAN_PREFIX + private_guardian_record.guardian_id
        key_ceremony_id = str(key_ceremony["_id"])
        file_path = path.join(getcwd(), "gui_private_keys", key_ceremony_id)
        file = to_file(private_guardian_record, file_name, file_path)
        self.log.warn(
            f"Guardian private data saved to {file}. This data should be carefully protected and never shared."
        )

    def get_ceremony(self, db: Database, id: str) -> dict[str, Any]:
        self.log.debug(f"getting key ceremony {id}")
        key_ceremony = self._key_ceremony_service.get(db, id)
        created_at_utc = key_ceremony["created_at"]
        key_ceremony["created_at_str"] = utc_to_str(created_at_utc)
        key_ceremony["can_join"] = self.can_join_key_ceremony(key_ceremony)
        return key_ceremony


def find_key(key_ceremony: Any, guardian_id: str) -> Any:
    keys = key_ceremony["keys"]
    return next(key for key in keys if key["owner_id"] == guardian_id)
