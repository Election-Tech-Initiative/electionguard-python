from enum import Enum


class KeyCeremonyStates(Enum):
    """A list of states for the key ceremony."""

    PendingGuardiansJoin = 1
    PendingAdminAnnounce = 2
    PendingGuardianBackups = 3
    PendingAdminToShareBackups = 4
    PendingGuardiansVerifyBackups = 5
    PendingAdminToPublishJointKey = 6
    Complete = 7
