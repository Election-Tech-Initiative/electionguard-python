from os import getcwd, path
from typing import Any

from electionguard import to_file
from electionguard.guardian import Guardian
from electionguard_gui.services.authorization_service import AuthorizationService
from electionguard_gui.services.db_service import DbService
from electionguard_gui.services.eel_log_service import EelLogService
from electionguard_gui.services.key_ceremony_service import KeyCeremonyService
from electionguard_gui.services.key_ceremony_stages.key_ceremony_stage_base import (
    KeyCeremonyStageBase,
)
from electionguard_gui.services.key_ceremony_state_service import (
    KeyCeremonyStateService,
)
from electionguard_gui.services.guardian_service import make_guardian
from electionguard_tools import GUARDIAN_PREFIX


class KeyCeremonyS1JoinService(KeyCeremonyStageBase):
    """Responsible for stage 1 of the key ceremony where guardians join"""

    def __init__(
        self,
        log_service: EelLogService,
        db_service: DbService,
        key_ceremony_service: KeyCeremonyService,
        auth_service: AuthorizationService,
        key_ceremony_state_service: KeyCeremonyStateService,
    ):
        super().__init__(
            log_service,
            db_service,
            key_ceremony_service,
            auth_service,
            key_ceremony_state_service,
        )

    def run(self, key_ceremony_id: str) -> None:
        db = self._db_service.get_db()

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

    def save_guardian(self, guardian: Guardian, key_ceremony: Any) -> None:
        private_guardian_record = guardian.export_private_data()
        file_name = GUARDIAN_PREFIX + private_guardian_record.guardian_id
        key_ceremony_id = str(key_ceremony["_id"])
        file_path = path.join(getcwd(), "gui_private_keys", key_ceremony_id)
        file = to_file(private_guardian_record, file_name, file_path)
        self.log.warn(
            f"Guardian private data saved to {file}. This data should be carefully protected and never shared."
        )
