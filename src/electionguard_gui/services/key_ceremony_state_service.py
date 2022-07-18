from typing import Any
from electionguard_gui.models.key_ceremony_states import KeyCeremonyStates
from electionguard_gui.services.eel_log_service import EelLogService
from electionguard_gui.services.service_base import ServiceBase


class KeyCeremonyStateService(ServiceBase):
    """Responsible for determining the state of the key ceremony"""

    log: EelLogService

    def __init__(self, log_service: EelLogService) -> None:
        self.log = log_service

    def get_key_ceremony_state(self, key_ceremony: Any) -> KeyCeremonyStates:
        guardians_joined = len(key_ceremony["guardians_joined"])
        guardian_count = key_ceremony["guardian_count"]
        other_keys = len(key_ceremony["other_keys"])
        backups = len(key_ceremony["backups"])
        expected_backups = pow(guardian_count, 2)
        self.log.debug(
            f"guardians: {guardians_joined}/{guardian_count}; "
            + f"other_keys: {other_keys}; "
            + f"backups: {backups}/{expected_backups}"
        )
        if guardians_joined < guardian_count:
            return KeyCeremonyStates.PendingGuardiansJoin
        if other_keys == 0:
            return KeyCeremonyStates.PendingAdminAnnounce
        if backups < expected_backups:
            return KeyCeremonyStates.PendingGuardianBackups
        return KeyCeremonyStates.PendingAdminToShareBackups


def get_key_ceremony_status(state: KeyCeremonyStates) -> str:
    if state == KeyCeremonyStates.PendingGuardiansJoin:
        return "waiting for guardians"
    if state == KeyCeremonyStates.PendingAdminAnnounce:
        return "waiting for admin to announce guardians"
    if state == KeyCeremonyStates.PendingGuardianBackups:
        return "waiting for guardians to create backups"
    if state == KeyCeremonyStates.PendingAdminToShareBackups:
        return "waiting for admin to share backups"
    if state == KeyCeremonyStates.PendingGuardiansVerifyBackups:
        return "waiting for guardians to verify backups"
    if state == KeyCeremonyStates.PendingAdminToPublishJointKey:
        return "waiting for admin to publish the joint key"
    if state == KeyCeremonyStates.Complete:
        return "key ceremony complete"
    raise Exception(f"unknown key ceremony state: {state}")
