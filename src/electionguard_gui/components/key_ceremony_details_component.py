import eel
from pymongo.database import Database


from electionguard_gui.services.key_ceremony_stages.key_ceremony_s1_join_service import (
    KeyCeremonyS1JoinService,
)
from electionguard_gui.services.key_ceremony_stages.key_ceremony_s2_announce_service import (
    KeyCeremonyS2AnnounceService,
)
from electionguard_gui.services.key_ceremony_stages.key_ceremony_s3_make_backup_service import (
    KeyCeremonyS3MakeBackupService,
)
from electionguard_gui.services.key_ceremony_stages.key_ceremony_s4_share_backup_service import (
    KeyCeremonyS4ShareBackupService,
)

from electionguard_gui.models.key_ceremony_dto import KeyCeremonyDto
from electionguard_gui.services.key_ceremony_state_service import (
    KeyCeremonyStateService,
    get_key_ceremony_status,
)
from electionguard_gui.models.key_ceremony_states import (
    KeyCeremonyStates,
)
from electionguard_gui.services.authorization_service import AuthorizationService
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.services.key_ceremony_service import (
    KeyCeremonyService,
)


class KeyCeremonyDetailsComponent(ComponentBase):
    """Responsible for retrieving key ceremony details"""

    _auth_service: AuthorizationService
    _ceremony_state_service: KeyCeremonyStateService
    _key_ceremony_s1_join_service: KeyCeremonyS1JoinService
    _key_ceremony_s2_announce_service: KeyCeremonyS2AnnounceService
    _key_ceremony_s3_make_backup_service: KeyCeremonyS3MakeBackupService
    _key_ceremony_s4_share_backup_service: KeyCeremonyS4ShareBackupService

    def __init__(
        self,
        key_ceremony_service: KeyCeremonyService,
        auth_service: AuthorizationService,
        key_ceremony_state_service: KeyCeremonyStateService,
        key_ceremony_s1_join_service: KeyCeremonyS1JoinService,
        key_ceremony_s2_announce_service: KeyCeremonyS2AnnounceService,
        key_ceremony_s3_make_backup_service: KeyCeremonyS3MakeBackupService,
        key_ceremony_s4_share_backup_service: KeyCeremonyS4ShareBackupService,
    ) -> None:
        super().__init__()
        self._key_ceremony_service = key_ceremony_service
        self._ceremony_state_service = key_ceremony_state_service
        self._auth_service = auth_service
        self._key_ceremony_s1_join_service = key_ceremony_s1_join_service
        self._key_ceremony_s2_announce_service = key_ceremony_s2_announce_service
        self._key_ceremony_s3_make_backup_service = key_ceremony_s3_make_backup_service
        self._key_ceremony_s4_share_backup_service = (
            key_ceremony_s4_share_backup_service
        )

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
            self._key_ceremony_s2_announce_service.run(db, key_ceremony)

        current_user_backups = key_ceremony.get_backup_count_for_user(current_user_id)
        current_user_backup_exists = current_user_backups > 0
        if (
            is_guardian
            and state == KeyCeremonyStates.PendingGuardianBackups
            and not current_user_backup_exists
        ):
            self._key_ceremony_s3_make_backup_service.run(db, key_ceremony)

        if is_admin and state == KeyCeremonyStates.PendingAdminToShareBackups:
            self._key_ceremony_s4_share_backup_service.run(db, key_ceremony)

        key_ceremony = self.get_ceremony(db, key_ceremony_id)
        new_state = self._ceremony_state_service.get_key_ceremony_state(key_ceremony)
        if state != new_state:
            self.log.debug(f"state changed from {state} to {new_state}")
        key_ceremony.status = get_key_ceremony_status(new_state)
        # pylint: disable=no-member
        eel.refresh_key_ceremony(key_ceremony.to_dict())

    def stop_watching_key_ceremony(self) -> None:
        self._key_ceremony_service.stop_watching()

    def join_key_ceremony(self, key_ceremony_id: str) -> None:
        db = self.db_service.get_db()
        key_ceremony = self.get_ceremony(db, key_ceremony_id)
        self._key_ceremony_s1_join_service.run(db, key_ceremony)

    def get_ceremony(self, db: Database, id: str) -> KeyCeremonyDto:
        key_ceremony = self._key_ceremony_service.get(db, id)
        key_ceremony.can_join = self.can_join_key_ceremony(key_ceremony)
        return key_ceremony
