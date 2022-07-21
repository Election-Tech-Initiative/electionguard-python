from gridfs import Database
from electionguard_gui.models.key_ceremony_dto import KeyCeremonyDto
from electionguard_gui.models.key_ceremony_states import KeyCeremonyStates
from electionguard_gui.services.guardian_service import (
    announce_guardians,
    make_mediator,
)
from electionguard_gui.services.key_ceremony_stages.key_ceremony_stage_base import (
    KeyCeremonyStageBase,
)


class KeyCeremonyS6PublishKeyService(KeyCeremonyStageBase):
    """
    Responsible for stage 6 of the key ceremony where admins receive verifications, publish
    a joint key, and generate a context.
    """

    def should_run(
        self, key_ceremony: KeyCeremonyDto, state: KeyCeremonyStates
    ) -> bool:
        is_admin = self._auth_service.is_admin()
        return is_admin and state == KeyCeremonyStates.PendingAdminToPublishJointKey

    def run(self, db: Database, key_ceremony: KeyCeremonyDto) -> None:
        current_user_id = self._auth_service.get_user_id()
        self.log.debug(f"receiving verifications for admin {current_user_id}")
        mediator = make_mediator(key_ceremony)
        announce_guardians(key_ceremony, mediator)
        mediator.receive_backups(key_ceremony.get_backups())
        verifications = key_ceremony.get_verifications()
        mediator.receive_backup_verifications(verifications)
        election_joint_key = mediator.publish_joint_key()
        if election_joint_key is None:
            raise Exception("Failed to publish joint key")
        self.log.info(f"joint key published: {election_joint_key.joint_public_key}")
        self._key_ceremony_service.append_joint_key(
            db, key_ceremony.id, election_joint_key
        )
        self._key_ceremony_service.set_complete(db, key_ceremony.id)
        # notify everyone that verifications completed and the joint key published
        self._key_ceremony_service.notify_changed(db, key_ceremony.id)
