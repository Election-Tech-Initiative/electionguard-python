from pymongo.database import Database
from electionguard_gui.models.key_ceremony_dto import KeyCeremonyDto
from electionguard_gui.models.key_ceremony_states import KeyCeremonyStates
from electionguard_gui.services.key_ceremony_stages.key_ceremony_stage_base import (
    KeyCeremonyStageBase,
)


class KeyCeremonyS3MakeBackupService(KeyCeremonyStageBase):
    """Responsible for stage 3 of the key ceremony where guardians create backups to send to the admin."""

    def should_run(
        self, key_ceremony: KeyCeremonyDto, state: KeyCeremonyStates
    ) -> bool:
        is_guardian = not self._auth_service.is_admin()
        current_user_id = self._auth_service.get_required_user_id()
        current_user_backups = key_ceremony.get_backup_count_for_user(current_user_id)
        current_user_backup_exists = current_user_backups > 0
        return (
            is_guardian
            and state == KeyCeremonyStates.PendingGuardianBackups
            and not current_user_backup_exists
        )

    def run(self, db: Database, key_ceremony: KeyCeremonyDto) -> None:
        current_user_id = self._auth_service.get_required_user_id()
        key_ceremony_id = key_ceremony.id
        self.log.debug(f"creating backups for guardian {current_user_id}")
        guardian = self._guardian_service.load_guardian_from_key_ceremony(
            current_user_id, key_ceremony
        )
        self._guardian_service.load_other_keys(key_ceremony, current_user_id, guardian)
        guardian.generate_election_partial_key_backups()
        backups = guardian.share_election_partial_key_backups()
        self._key_ceremony_service.append_backups(db, key_ceremony_id, backups)
        # notify the admin that a new guardian has backups
        self._key_ceremony_service.notify_changed(db, key_ceremony_id)
