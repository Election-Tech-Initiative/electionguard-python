from typing import Iterable, List, Optional

from .auxiliary import AuxiliaryDecrypt, AuxiliaryEncrypt
from .data_store import DataStore
from .guardian import Guardian
from .key_ceremony import (
    AuxiliaryPublicKey,
    CeremonyDetails,
    ElectionJointKey,
    ElectionPartialKeyBackup,
    ElectionPartialKeyChallenge,
    ElectionPartialKeyVerification,
    ElectionPublicKey,
    GuardianPair,
    PublicKeySet,
    combine_election_public_keys,
)
from .logs import log_warning
from .rsa import rsa_decrypt, rsa_encrypt
from .types import GUARDIAN_ID


class KeyCeremonyMediator:
    """
    KeyCeremonyMediator for assisting communication between guardians 
    """

    ceremony_details: CeremonyDetails

    _auxiliary_public_keys: DataStore[GUARDIAN_ID, AuxiliaryPublicKey]
    _election_public_keys: DataStore[GUARDIAN_ID, ElectionPublicKey]
    _election_partial_key_backups: DataStore[GuardianPair, ElectionPartialKeyBackup]
    _election_partial_key_challenges: DataStore[
        GuardianPair, ElectionPartialKeyChallenge
    ]
    _election_partial_key_verifications: DataStore[
        GuardianPair, ElectionPartialKeyVerification
    ]
    _guardians: List[Guardian] = []

    def __init__(self, ceremony_details: CeremonyDetails):
        self.ceremony_details = ceremony_details
        self._auxiliary_public_keys = DataStore[GUARDIAN_ID, AuxiliaryPublicKey]()
        self._election_public_keys = DataStore[GUARDIAN_ID, ElectionPublicKey]()
        self._election_partial_key_backups = DataStore[
            GuardianPair, ElectionPartialKeyBackup
        ]()
        self._election_partial_key_verifications = DataStore[
            GuardianPair, ElectionPartialKeyVerification
        ]()
        self._election_partial_key_challenges = DataStore[
            GuardianPair, ElectionPartialKeyChallenge
        ]()

    def announce(self, guardian: Guardian) -> None:
        """
        Announce the guardian as present and participating the Key Ceremony
        :param guardian: The guardian to announce
        """
        self.confirm_presence_of_guardian(guardian.share_public_keys())
        self._guardians.append(guardian)

        # When all guardians have announced, share the public keys among them
        if self.all_guardians_in_attendance():
            for sender in self._guardians:
                for recipient in self._guardians:
                    if sender.object_id != recipient.object_id:
                        recipient.save_guardian_public_keys(sender.share_public_keys())

    def orchestrate(
        self, encrypt: AuxiliaryEncrypt = rsa_encrypt
    ) -> Optional[List[Guardian]]:
        """
        Orchestrate the KLey Ceremony by sharing keys among the anounced guardians

        :param encrypt: Auxiliary encrypt function
        :return: a collection of guardians, or None if there is an error
        """
        if not self.all_guardians_in_attendance():
            return None

        # Partial Key Backup Generation
        for guardian in self._guardians:
            guardian.generate_election_partial_key_backups(encrypt)

        # Share Partial Key Backup
        for sender in self._guardians:
            for recipient in self._guardians:
                if sender.object_id != recipient.object_id:
                    backup = sender.share_election_partial_key_backup(
                        recipient.object_id
                    )

                    if backup is not None:
                        self.receive_election_partial_key_backup(backup)
                    else:
                        log_warning(
                            f"orchestrate failed sender {sender.object_id} could not share backup with recipient: {recipient.object_id}"
                        )
                        return None

        # Save the backups
        if self.all_election_partial_key_backups_available:
            for recipient_guardian in self._guardians:
                backups = self.share_election_partial_key_backups_to_guardian(
                    recipient_guardian.object_id
                )
                for backup in backups:
                    recipient_guardian.save_election_partial_key_backup(backup)

        return self._guardians

    def verify(self, decrypt: AuxiliaryDecrypt = rsa_decrypt) -> bool:
        """
        Verify that the guardians correctly shared keys
        :param decrypt: Auxiliary decrypt function
        :return: True if verification succeds, else False
        """
        for recipient in self._guardians:
            for sender in self._guardians:
                if sender.object_id != recipient.object_id:
                    verification = recipient.verify_election_partial_key_backup(
                        sender.object_id, decrypt
                    )
                    if verification is not None:
                        self.receive_election_partial_key_verification(verification)
                    else:
                        log_warning(
                            f"verify failed recipient {recipient.object_id} could not verify backup from sender: {sender.object_id}"
                        )
                        return False

        return (
            self.all_election_partial_key_verifications_received()
            and self.all_election_partial_key_backups_verified()
        )

    def reset(self, ceremony_details: CeremonyDetails) -> None:
        """
        Reset mediator to initial state
        :param ceremony_details: Ceremony details of election
        """
        self.ceremony_details = ceremony_details
        self._auxiliary_public_keys.clear()
        self._election_public_keys.clear()
        self._election_partial_key_backups.clear()
        self._election_partial_key_challenges.clear()
        self._election_partial_key_verifications.clear()
        self._guardians.clear()

    # Attendance
    def confirm_presence_of_guardian(self, public_key_set: PublicKeySet) -> None:
        """
        Confirm presence of guardian by passing their public key set
        :param public_key_set: Public key set
        """
        self.receive_auxiliary_public_key(
            AuxiliaryPublicKey(
                public_key_set.owner_id,
                public_key_set.sequence_order,
                public_key_set.auxiliary_public_key,
            )
        )
        self.receive_election_public_key(
            ElectionPublicKey(
                public_key_set.owner_id,
                public_key_set.election_public_key_proof,
                public_key_set.election_public_key,
            ),
        )

    def all_guardians_in_attendance(self) -> bool:
        """
        Check the attendance of all the guardians expected
        :return: True if all guardians in attendance
        """
        return (
            self.all_auxiliary_public_keys_available()
            and self.all_election_public_keys_available()
        )

    def share_guardians_in_attendance(self) -> Iterable[GUARDIAN_ID]:
        """
        Share a list of all the guardians in attendance
        :return: list of guardians ids
        """
        return self._election_public_keys.keys()

    # Auxiliary Public Keys
    def receive_auxiliary_public_key(self, public_key: AuxiliaryPublicKey) -> None:
        """
        Receive auxiliary public key from guardian
        :param public_key: Auxiliary public key
        """
        self._auxiliary_public_keys.set(public_key.owner_id, public_key)

    def all_auxiliary_public_keys_available(self) -> bool:
        """
        True if all auxiliary public key for all guardians available
        :return: All auxiliary public backups for all guardians available
        """
        return (
            len(self._auxiliary_public_keys)
            == self.ceremony_details.number_of_guardians
        )

    def share_auxiliary_public_keys(self) -> Iterable[AuxiliaryPublicKey]:
        """
        Share all currently stored auxiliary public keys for all guardians
        :return: list of auxiliary public keys
        """
        return self._auxiliary_public_keys.values()

    # Election Public Keys
    def receive_election_public_key(self, public_key: ElectionPublicKey) -> None:
        """
        Receive election public key from guardian
        :param public_key: election public key
        """
        self._election_public_keys.set(public_key.owner_id, public_key)

    def all_election_public_keys_available(self) -> bool:
        """
        True if all election public keys for all guardians available
        :return: All election public keys for all guardians available
        """
        return (
            len(self._election_public_keys) == self.ceremony_details.number_of_guardians
        )

    def share_election_public_keys(self) -> Iterable[ElectionPublicKey]:
        """
        Share all currently stored election public keys for all guardians
        :return: list of election public keys
        """
        return self._election_public_keys.values()

    # Election Partial Key Backups
    def receive_election_partial_key_backup(
        self, backup: ElectionPartialKeyBackup
    ) -> bool:
        """
        Receive election partial key backup from guardian
        :param backup: Election partial key backup
        :return: boolean indicating success or failure
        """
        if backup.owner_id == backup.designated_id:
            return False
        self._election_partial_key_backups.set(
            GuardianPair(backup.owner_id, backup.designated_id), backup
        )
        return True

    def all_election_partial_key_backups_available(self) -> bool:
        """
        True if all election partial key backups for all guardians available
        :return: All election partial key backups for all guardians available
        """
        required_backups_per_guardian = self.ceremony_details.number_of_guardians - 1
        return (
            len(self._election_partial_key_backups)
            == required_backups_per_guardian * self.ceremony_details.number_of_guardians
        )

    def share_election_partial_key_backups_to_guardian(
        self, guardian_id: GUARDIAN_ID
    ) -> List[ElectionPartialKeyBackup]:
        """
        Share all election partial key backups for designated guardian
        :param guardian_id: Recipients guardian id
        :return: List of guardians designated backups
        """
        backups: List[ElectionPartialKeyBackup] = []
        for current_guardian_id in self.share_guardians_in_attendance():
            if guardian_id != current_guardian_id:
                backup = self._election_partial_key_backups.get(
                    GuardianPair(current_guardian_id, guardian_id)
                )
                if backup is not None:
                    backups.append(backup)
        return backups

    # Partial Key Verifications
    def receive_election_partial_key_verification(
        self, verification: ElectionPartialKeyVerification
    ) -> None:
        """
        Receive election partial key verification from guardian
        :param verification: Election partial key verification
        """
        if verification.owner_id == verification.designated_id:
            return
        self._election_partial_key_verifications.set(
            GuardianPair(verification.owner_id, verification.designated_id),
            verification,
        )

    def all_election_partial_key_verifications_received(self) -> bool:
        """
        True if all election partial key verifications recieved
        :return: All election partial key verifications received
        """
        required_verifications_per_guardian = (
            self.ceremony_details.number_of_guardians - 1
        )
        return (
            len(self._election_partial_key_verifications)
            == required_verifications_per_guardian
            * self.ceremony_details.number_of_guardians
        )

    def all_election_partial_key_backups_verified(self) -> bool:
        """
        True if all election partial key backups verified
        :return: All election partial key backups verified
        """
        if not self.all_election_partial_key_verifications_received():
            return False
        for verification in self._election_partial_key_verifications.values():
            if not verification.verified:
                return False
        return True

    # Partial Key Challenges
    def share_failed_partial_key_verifications(self) -> List[GuardianPair]:
        """
        Share list of guardians with failed partial key backup verifications
        :return: List of guardian pairs with failed verifications
        """
        failed_verifications: List[GuardianPair] = []
        for pair, verification in self._election_partial_key_verifications.items():
            if not verification.verified:
                failed_verifications.append(pair)
        return failed_verifications

    def share_missing_election_partial_key_challenges(self) -> List[GuardianPair]:
        """
        Share list of guardians with missing election partial key challenges
        :return: List of guardian pairs with failed verifications and no challenges
        """
        failed_verifications = self.share_failed_partial_key_verifications()
        for pair in self._election_partial_key_challenges.keys():
            failed_verifications.remove(pair)
        return failed_verifications

    def receive_election_partial_key_challenge(
        self, challenge: ElectionPartialKeyChallenge
    ) -> None:
        """
        Receive an election partial key challenge from a guardian with a failed verification
        :param challenge: Election partial key challenge
        """
        self._election_partial_key_challenges.set(
            GuardianPair(challenge.owner_id, challenge.designated_id), challenge
        )

    def share_open_election_partial_key_challenges(
        self,
    ) -> List[ElectionPartialKeyChallenge]:
        """
        Share all open election partial key challenges with guardians
        :return: List of open election partial key challenges 
        """
        return list(self._election_partial_key_challenges.values())

    # Publish Joint Key
    def publish_joint_key(self) -> Optional[ElectionJointKey]:
        """
        Publish joint election key from the public keys of all guardians
        :return: Optional joint key for election
        """
        if not self.all_election_public_keys_available():
            return None
        if not self.all_election_partial_key_backups_verified():
            return None
        return combine_election_public_keys(self._election_public_keys)
