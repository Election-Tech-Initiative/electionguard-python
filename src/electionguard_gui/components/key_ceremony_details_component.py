from os import getcwd, path
from typing import Any, List
import eel
from pymongo.database import Database

from electionguard import to_file
from electionguard.guardian import Guardian, PrivateGuardianRecord
from electionguard.key_ceremony import CeremonyDetails, ElectionPartialKeyBackup
from electionguard.key_ceremony_mediator import KeyCeremonyMediator
from electionguard.serialize import from_file
from electionguard.utils import get_optional
from electionguard_tools.helpers.export import GUARDIAN_PREFIX

from electionguard_gui.models.key_ceremony_dto import KeyCeremonyDto
from electionguard_gui.services.key_ceremony_state_service import (
    KeyCeremonyStateService,
    get_key_ceremony_status,
)
from electionguard_gui.models.key_ceremony_states import (
    KeyCeremonyStates,
)
from electionguard_gui.services.db_serialization_service import (
    backup_to_dict,
    public_key_to_dict,
)
from electionguard_gui.services.authorization_service import AuthorizationService
from electionguard_gui.services.guardian_service import make_guardian
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.services.key_ceremony_service import (
    KeyCeremonyService,
)


class KeyCeremonyDetailsComponent(ComponentBase):
    """Responsible for retrieving key ceremony details"""

    _auth_service: AuthorizationService
    _ceremony_state_service: KeyCeremonyStateService

    def __init__(
        self,
        key_ceremony_service: KeyCeremonyService,
        auth_service: AuthorizationService,
        key_ceremony_state_service: KeyCeremonyStateService,
    ) -> None:
        super().__init__()
        self._key_ceremony_service = key_ceremony_service
        self._ceremony_state_service = key_ceremony_state_service
        self._auth_service = auth_service

    def expose(self) -> None:
        eel.expose(self.join_key_ceremony)
        eel.expose(self.watch_key_ceremony)
        eel.expose(self.stop_watching_key_ceremony)

    def can_join_key_ceremony(self, key_ceremony: KeyCeremonyDto) -> bool:
        user_id = self._auth_service.get_user_id()
        already_joined = user_id in key_ceremony.guardians_joined
        is_admin = self._auth_service.is_admin()
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
        current_user_id = self._auth_service.get_user_id()
        self.log.debug(
            f"on_key_ceremony_changed key_ceremony_id: '{key_ceremony_id}', current_user_id: '{current_user_id}'"
        )
        is_admin = self._auth_service.is_admin()
        is_guardian = not is_admin
        db = self.db_service.get_db()
        key_ceremony = self.get_ceremony(db, key_ceremony_id)
        state = self._ceremony_state_service.get_key_ceremony_state(key_ceremony)
        self.log.debug(f"{key_ceremony_id} state = '{state}'")
        if is_admin and state == KeyCeremonyStates.PendingAdminAnnounce:
            self.log.info("all guardians have joined, announcing guardians")
            other_keys = self.announce(key_ceremony)
            self.log.debug("saving other_keys")
            self._key_ceremony_service.append_other_key(db, key_ceremony_id, other_keys)
            # this notify_changed occurs inside watch_key_ceremonies and thus may
            #       produce an unnecessary UI refresh for the admin
            self._key_ceremony_service.notify_changed(db, key_ceremony_id)
            # todo #689 wait until all guardians have backups

        current_user_backups = key_ceremony.get_backup_count_for_user(current_user_id)
        current_user_backup_exists = current_user_backups > 0
        if (
            is_guardian
            and state == KeyCeremonyStates.PendingGuardianBackups
            and not current_user_backup_exists
        ):
            self.log.debug(f"creating backups for guardian {current_user_id}")
            guardian = self.load_guardian(current_user_id, key_ceremony)

            current_user_other_keys = key_ceremony.find_other_keys_for_user(
                current_user_id
            )
            for other_key in current_user_other_keys:
                other_user = other_key.owner_id
                self.log.debug(
                    f"saving other_key from {other_user} for {current_user_id}"
                )
                guardian.save_guardian_key(other_key)
            guardian.generate_election_partial_key_backups()
            backups = guardian.share_election_partial_key_backups()
            self._key_ceremony_service.append_backups(db, key_ceremony_id, backups)
            # notify the admin that a new guardian has backups
            self._key_ceremony_service.notify_changed(db, key_ceremony_id)

        if is_admin and state == KeyCeremonyStates.PendingAdminToShareBackups:
            self.log.debug(f"sharing backups for admin {current_user_id}")
            shared_backups = self.share_backups(key_ceremony)
            self._key_ceremony_service.append_shared_backups(
                db, key_ceremony.id, shared_backups
            )
            self._key_ceremony_service.notify_changed(db, key_ceremony_id)

        key_ceremony = self.get_ceremony(db, key_ceremony_id)
        new_state = self._ceremony_state_service.get_key_ceremony_state(key_ceremony)
        if state != new_state:
            self.log.debug(f"state changed from {state} to {new_state}")
        key_ceremony.status = get_key_ceremony_status(new_state)
        # pylint: disable=no-member
        eel.refresh_key_ceremony(key_ceremony.to_dict())

    def share_backups(self, key_ceremony: KeyCeremonyDto) -> List[Any]:
        mediator = self.make_mediator(key_ceremony)
        self.announce_guardians(key_ceremony, mediator)
        mediator.receive_backups(key_ceremony.get_backups())
        shared_backups = []
        for guardian_id in key_ceremony.guardians_joined:
            self.log.debug(f"sharing backups for guardian {guardian_id}")
            guardian_backups = mediator.share_backups(guardian_id)
            backups_as_dict = [backup_to_dict(backup) for backup in guardian_backups]
            shared_backups.append({"owner_id": guardian_id, "backups": backups_as_dict})
        return shared_backups

    def make_mediator(self, key_ceremony: KeyCeremonyDto) -> KeyCeremonyMediator:
        quorum = key_ceremony.quorum
        guardian_count = key_ceremony.guardian_count
        ceremony_details = CeremonyDetails(guardian_count, quorum)
        mediator: KeyCeremonyMediator = KeyCeremonyMediator(
            "mediator_1", ceremony_details
        )
        return mediator

    def announce_guardians(
        self, key_ceremony: KeyCeremonyDto, mediator: KeyCeremonyMediator
    ) -> None:
        for guardian_id in key_ceremony.guardians_joined:
            key = key_ceremony.find_key(guardian_id)
            self.log.debug(f"announcing {guardian_id}, {key}")
            mediator.announce(key)

    def announce(self, key_ceremony: KeyCeremonyDto) -> List[dict[str, Any]]:
        other_keys = []
        mediator = self.make_mediator(key_ceremony)
        self.announce_guardians(key_ceremony, mediator)
        for guardian_id in key_ceremony.guardians_joined:
            other_guardian_keys = get_optional(mediator.share_announced(guardian_id))
            other_keys.append(
                {
                    "owner_id": guardian_id,
                    "other_keys": [
                        public_key_to_dict(key) for key in other_guardian_keys
                    ],
                }
            )
        return other_keys

    def stop_watching_key_ceremony(self) -> None:
        self._key_ceremony_service.stop_watching()

    def join_key_ceremony(self, key_ceremony_id: str) -> None:
        db = self.db_service.get_db()

        # append the current user's id to the list of guardians
        user_id = self._auth_service.get_user_id()
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

    def load_guardian(self, guardian_id: str, key_ceremony: KeyCeremonyDto) -> Guardian:
        file_name = GUARDIAN_PREFIX + guardian_id + ".json"
        file_path = path.join(getcwd(), "gui_private_keys", key_ceremony.id, file_name)
        self.log.debug(f"loading guardian from {file_path}")
        private_guardian_record = from_file(PrivateGuardianRecord, file_path)
        return Guardian.from_private_record(
            private_guardian_record,
            key_ceremony.guardian_count,
            key_ceremony.quorum,
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

    def get_ceremony(self, db: Database, id: str) -> KeyCeremonyDto:
        key_ceremony = self._key_ceremony_service.get(db, id)
        key_ceremony_db = KeyCeremonyDto(key_ceremony)
        key_ceremony_db.can_join = self.can_join_key_ceremony(key_ceremony_db)
        return key_ceremony_db
