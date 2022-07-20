from electionguard_gui.models.key_ceremony_dto import KeyCeremonyDto
from electionguard_gui.models.key_ceremony_states import KeyCeremonyStates
from electionguard_gui.services.eel_log_service import EelLogService
from electionguard_gui.services.service_base import ServiceBase


class KeyCeremonyStateService(ServiceBase):
    """Responsible for determining the state of the key ceremony"""

    log: EelLogService

    def __init__(self, log_service: EelLogService) -> None:
        self.log = log_service

    # pylint: disable=too-many-return-statements
    def get_key_ceremony_state(self, key_ceremony: KeyCeremonyDto) -> KeyCeremonyStates:
        guardians_joined = len(key_ceremony.guardians_joined)
        guardian_count = key_ceremony.guardian_count
        other_keys = len(key_ceremony.other_keys)
        backups = len(key_ceremony.backups)
        shared_backups = len(key_ceremony.shared_backups)
        expected_backups = pow(guardian_count, 2)
        verifications = len(key_ceremony.verifications)
        expected_verifications = pow(guardian_count, 2) - guardian_count
        self.log.debug(
            f"guardians: {guardians_joined}/{guardian_count}; "
            + f"other_keys: {other_keys}/{guardian_count}; "
            + f"backups: {backups}/{expected_backups}; "
            + f"shared_backups: {shared_backups}/{guardian_count}; "
            + f"verifications: {verifications}/{expected_verifications}"
        )
        if guardians_joined < guardian_count:
            return KeyCeremonyStates.PendingGuardiansJoin
        if other_keys == 0:
            return KeyCeremonyStates.PendingAdminAnnounce
        if backups < expected_backups:
            return KeyCeremonyStates.PendingGuardianBackups
        if shared_backups == 0:
            return KeyCeremonyStates.PendingAdminToShareBackups
        if verifications < expected_verifications:
            return KeyCeremonyStates.PendingGuardiansVerifyBackups
        if not key_ceremony.joint_key_exists():
            return KeyCeremonyStates.PendingAdminToPublishJointKey
        return KeyCeremonyStates.Complete


status_descriptions = {
    KeyCeremonyStates.PendingGuardiansJoin: "waiting for guardians",
    KeyCeremonyStates.PendingAdminAnnounce: "waiting for admin to announce guardians",
    KeyCeremonyStates.PendingGuardianBackups: "waiting for guardians to create backups",
    KeyCeremonyStates.PendingAdminToShareBackups: "waiting for admin to share backups",
    KeyCeremonyStates.PendingGuardiansVerifyBackups: "waiting for guardians to verify backups",
    KeyCeremonyStates.PendingAdminToPublishJointKey: "waiting for admin to publish the joint key",
    KeyCeremonyStates.Complete: "key ceremony complete",
}


def get_key_ceremony_status(state: KeyCeremonyStates) -> str:
    return status_descriptions[state]
