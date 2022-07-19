from os import getcwd, path
from pymongo.database import Database
from electionguard import Guardian
from electionguard.guardian import PrivateGuardianRecord
from electionguard.serialize import from_file
from electionguard_gui.models.key_ceremony_dto import KeyCeremonyDto
from electionguard_gui.services.key_ceremony_stages.key_ceremony_stage_base import (
    KeyCeremonyStageBase,
)

from electionguard_tools import GUARDIAN_PREFIX


class KeyCeremonyS3MakeBackupService(KeyCeremonyStageBase):
    """Responsible for stage 3 of the key ceremony where guardians create backups to send to the admin."""

    def run(self, db: Database, key_ceremony: KeyCeremonyDto) -> None:
        current_user_id = self._auth_service.get_user_id()
        key_ceremony_id = key_ceremony.id
        self.log.debug(f"creating backups for guardian {current_user_id}")
        guardian = self.load_guardian(current_user_id, key_ceremony)

        current_user_other_keys = key_ceremony.find_other_keys_for_user(current_user_id)
        for other_key in current_user_other_keys:
            other_user = other_key.owner_id
            self.log.debug(f"saving other_key from {other_user} for {current_user_id}")
            guardian.save_guardian_key(other_key)
        guardian.generate_election_partial_key_backups()
        backups = guardian.share_election_partial_key_backups()
        self._key_ceremony_service.append_backups(db, key_ceremony_id, backups)
        # notify the admin that a new guardian has backups
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
