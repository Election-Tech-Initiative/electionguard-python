import traceback
from typing import List
import eel
from pymongo.database import Database
from electionguard_gui.eel_utils import eel_fail, eel_success


from electionguard_gui.services.key_ceremony_stages import (
    KeyCeremonyStageBase,
    KeyCeremonyS1JoinService,
    KeyCeremonyS2AnnounceService,
    KeyCeremonyS3MakeBackupService,
    KeyCeremonyS4ShareBackupService,
    KeyCeremonyS5VerifyBackupService,
    KeyCeremonyS6PublishKeyService,
)

from electionguard_gui.models.key_ceremony_dto import KeyCeremonyDto
from electionguard_gui.services.key_ceremony_state_service import (
    KeyCeremonyStateService,
    get_key_ceremony_status,
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
    key_ceremony_watch_stages: List[KeyCeremonyStageBase]

    def __init__(
        self,
        key_ceremony_service: KeyCeremonyService,
        auth_service: AuthorizationService,
        key_ceremony_state_service: KeyCeremonyStateService,
        key_ceremony_s1_join_service: KeyCeremonyS1JoinService,
        key_ceremony_s2_announce_service: KeyCeremonyS2AnnounceService,
        key_ceremony_s3_make_backup_service: KeyCeremonyS3MakeBackupService,
        key_ceremony_s4_share_backup_service: KeyCeremonyS4ShareBackupService,
        key_ceremony_s5_verification_service: KeyCeremonyS5VerifyBackupService,
        key_ceremony_s6_publish_key_service: KeyCeremonyS6PublishKeyService,
    ) -> None:
        super().__init__()
        self._key_ceremony_service = key_ceremony_service
        self._ceremony_state_service = key_ceremony_state_service
        self._auth_service = auth_service
        self._key_ceremony_s1_join_service = key_ceremony_s1_join_service
        self.key_ceremony_watch_stages = [
            key_ceremony_s2_announce_service,
            key_ceremony_s3_make_backup_service,
            key_ceremony_s4_share_backup_service,
            key_ceremony_s5_verification_service,
            key_ceremony_s6_publish_key_service,
        ]

    def expose(self) -> None:
        eel.expose(self.join_key_ceremony)
        eel.expose(self.watch_key_ceremony)
        eel.expose(self.stop_watching_key_ceremony)

    def watch_key_ceremony(self, key_ceremony_id: str) -> None:
        db = self._db_service.get_db()
        # retrieve and send the key ceremony to the client
        self.on_key_ceremony_changed(key_ceremony_id)
        self._log.debug(f"watching key ceremony '{key_ceremony_id}'")
        # start watching for key ceremony changes from guardians
        self._key_ceremony_service.watch_key_ceremonies(
            db, key_ceremony_id, self.on_key_ceremony_changed
        )

    def on_key_ceremony_changed(self, key_ceremony_id: str) -> None:
        try:
            self._log.debug(
                f"on_key_ceremony_changed key_ceremony_id: '{key_ceremony_id}'"
            )
            db = self._db_service.get_db()
            key_ceremony = self.get_ceremony(db, key_ceremony_id)
            state = self._ceremony_state_service.get_key_ceremony_state(key_ceremony)
            self._log.debug(f"{key_ceremony_id} state = '{state}'")

            for stage in self.key_ceremony_watch_stages:
                if stage.should_run(key_ceremony, state):
                    stage.run(db, key_ceremony)
                    break

            key_ceremony = self.get_ceremony(db, key_ceremony_id)
            new_state = self._ceremony_state_service.get_key_ceremony_state(
                key_ceremony
            )
            if state != new_state:
                self._log.debug(f"state changed from {state} to {new_state}")
            key_ceremony.status = get_key_ceremony_status(new_state)
            result = key_ceremony.to_dict()
            # pylint: disable=no-member
            eel.refresh_key_ceremony(eel_success(result))
        # pylint: disable=broad-except
        except Exception as e:
            self._log.error(e)
            traceback.print_exc()
            # pylint: disable=no-member
            eel.refresh_key_ceremony(eel_fail(str(e)))

    def stop_watching_key_ceremony(self) -> None:
        self._key_ceremony_service.stop_watching()

    def join_key_ceremony(self, key_ceremony_id: str) -> None:
        db = self._db_service.get_db()
        key_ceremony = self.get_ceremony(db, key_ceremony_id)
        self._key_ceremony_s1_join_service.run(db, key_ceremony)

    def get_ceremony(self, db: Database, id: str) -> KeyCeremonyDto:
        key_ceremony = self._key_ceremony_service.get(db, id)
        key_ceremony.can_join = self.can_join_key_ceremony(key_ceremony)
        return key_ceremony

    def can_join_key_ceremony(self, key_ceremony: KeyCeremonyDto) -> bool:
        user_id = self._auth_service.get_user_id()
        already_joined = user_id in key_ceremony.guardians_joined
        is_admin = self._auth_service.is_admin()
        return not already_joined and not is_admin
