from typing import Any, List
from pymongo.database import Database
from electionguard_gui.models.key_ceremony_dto import KeyCeremonyDto
from electionguard_gui.models.key_ceremony_states import KeyCeremonyStates
from electionguard_gui.services.db_serialization_service import backup_to_dict
from electionguard_gui.services.guardian_service import (
    announce_guardians,
    make_mediator,
)
from electionguard_gui.services.key_ceremony_stages.key_ceremony_stage_base import (
    KeyCeremonyStageBase,
)


class KeyCeremonyS4ShareBackupService(KeyCeremonyStageBase):
    """
    Responsible for stage 4 of the key ceremony where admins receive backups and share them
    back to guardians for verification.
    """

    def should_run(
        self, key_ceremony: KeyCeremonyDto, state: KeyCeremonyStates
    ) -> bool:
        is_admin: bool = self._auth_service.is_admin()
        return is_admin and state == KeyCeremonyStates.PendingAdminToShareBackups

    def run(self, db: Database, key_ceremony: KeyCeremonyDto) -> None:
        current_user_id = self._auth_service.get_user_id()
        self.log.debug(f"sharing backups for admin {current_user_id}")
        shared_backups = self.share_backups(key_ceremony)
        self._key_ceremony_service.append_shared_backups(
            db, key_ceremony.id, shared_backups
        )
        self._key_ceremony_service.notify_changed(db, key_ceremony.id)

    def share_backups(self, key_ceremony: KeyCeremonyDto) -> List[Any]:
        mediator = make_mediator(key_ceremony)
        announce_guardians(key_ceremony, mediator)
        mediator.receive_backups(key_ceremony.get_backups())
        shared_backups = []
        for guardian_id in key_ceremony.guardians_joined:
            self.log.debug(f"sharing backups for guardian {guardian_id}")
            guardian_backups = mediator.share_backups(guardian_id)
            if guardian_backups is None:
                raise Exception("Error sharing backups")
            backups_as_dict = [backup_to_dict(backup) for backup in guardian_backups]
            shared_backups.append({"owner_id": guardian_id, "backups": backups_as_dict})
        return shared_backups
