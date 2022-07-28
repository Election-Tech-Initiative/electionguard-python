from typing import List
from pymongo.database import Database
from electionguard.key_ceremony import ElectionPartialKeyVerification
from electionguard_gui.models.key_ceremony_dto import KeyCeremonyDto
from electionguard_gui.models.key_ceremony_states import KeyCeremonyStates
from electionguard_gui.services.key_ceremony_stages.key_ceremony_stage_base import (
    KeyCeremonyStageBase,
)


class KeyCeremonyS5VerifyBackupService(KeyCeremonyStageBase):
    """Responsible for stage 5 of the key ceremony where guardians verify backups."""

    def should_run(
        self, key_ceremony: KeyCeremonyDto, state: KeyCeremonyStates
    ) -> bool:
        is_guardian = not self._auth_service.is_admin()
        current_user_id = self._auth_service.get_required_user_id()
        current_user_verifications = key_ceremony.get_verification_count_for_user(
            current_user_id
        )
        current_user_verification_exists = current_user_verifications > 0
        return (
            is_guardian
            and state == KeyCeremonyStates.PendingGuardiansVerifyBackups
            and not current_user_verification_exists
        )

    def run(self, db: Database, key_ceremony: KeyCeremonyDto) -> None:
        current_user_id = self._auth_service.get_required_user_id()
        shared_backups = key_ceremony.get_shared_backups_for_guardian(current_user_id)
        guardian = self._guardian_service.load_guardian_from_key_ceremony(
            current_user_id, key_ceremony
        )
        self._guardian_service.load_other_keys(key_ceremony, current_user_id, guardian)
        verifications: List[ElectionPartialKeyVerification] = []
        for backup in shared_backups:
            self.log.debug(
                f"verifying backup from {backup.owner_id} to {current_user_id}"
            )
            guardian.save_election_partial_key_backup(backup)
            verification = guardian.verify_election_partial_key_backup(backup.owner_id)
            if verification is None:
                raise Exception("Error verifying backup")
            verifications.append(verification)
        self._key_ceremony_service.append_verifications(
            db, key_ceremony.id, verifications
        )
        # notify the admin that a new verification was created
        self._key_ceremony_service.notify_changed(db, key_ceremony.id)
