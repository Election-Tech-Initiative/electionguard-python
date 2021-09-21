from typing import Dict, List

from tests.base_test_case import BaseTestCase

from electionguard.auxiliary import AuxiliaryKeyPair
from electionguard.key_ceremony import (
    ElectionKeyPair,
    ElectionPartialKeyBackup,
    ElectionPartialKeyVerification,
    PublicKeySet,
    combine_election_public_keys,
    generate_election_key_pair,
    generate_election_partial_key_backup,
    generate_election_partial_key_challenge,
    generate_rsa_auxiliary_key_pair,
    verify_election_partial_key_backup,
    verify_election_partial_key_challenge,
)
from electionguard.type import GUARDIAN_ID
from electionguard_tools.helpers.identity_encrypt import identity_auxiliary_encrypt


class TestKeyCeremony(BaseTestCase):
    """
    Test the key ceremony entirely from a functional sense
    This demonstrates that no stateful models are required and
    allows users to see the full flow utilizing only the core methods.
    """

    # Basic Types
    SENDER_ID = GUARDIAN_ID
    RECEIVER_ID = GUARDIAN_ID

    # Key Ceremony Inputs
    NUMBER_OF_GUARDIANS = 5
    QUORUM = 3

    # ROUND 1
    election_key_pairs: Dict[str, ElectionKeyPair] = {}
    auxiliary_key_pairs: Dict[str, AuxiliaryKeyPair] = {}
    guardian_keys: Dict[str, PublicKeySet] = {}

    # ROUND 2
    sent_backups: Dict[SENDER_ID, List[ElectionPartialKeyBackup]] = {}
    received_backups: Dict[RECEIVER_ID, List[ElectionPartialKeyBackup]] = {}

    # ROUND 3
    sent_verifications: Dict[SENDER_ID, List[ElectionPartialKeyVerification]] = {}
    received_verifications: Dict[RECEIVER_ID, List[ElectionPartialKeyVerification]] = {}

    def test_key_ceremony(self) -> None:
        # Determine guardian id and sequence order
        guardian_sequence_orders = [*range(1, self.NUMBER_OF_GUARDIANS + 1)]
        guardian_ids = [f"guardian_{i}" for i in guardian_sequence_orders]

        # ROUND 1 - SHARE KEYS
        # Each guardian generates their own keys
        for guardian_id, sequence_order in zip(guardian_ids, guardian_sequence_orders):
            self._guardian_generates_keys(guardian_id, sequence_order)
        self.assertEqual(len(self.election_key_pairs), self.NUMBER_OF_GUARDIANS)
        self.assertEqual(len(self.auxiliary_key_pairs), self.NUMBER_OF_GUARDIANS)

        # Each guardian shares their keys
        for guardian_id in guardian_ids:
            self._guardian_share_keys(guardian_id)
        self.assertEqual(len(self.guardian_keys), self.NUMBER_OF_GUARDIANS)

        # ROUND 2 - SHARE BACKUPS
        # Each guardian generates and shares their backups
        for guardian_id in guardian_ids:
            self._guardian_generates_backups(guardian_id)
            self._guardian_shares_backups(guardian_id)

        # ROUND 3 - VERIFY BACKUPS
        # Each guardian verifies the backups they received
        # then shares each of the verifications to the owner of the key
        for guardian_id in guardian_ids:
            self._guardian_verifies_backups(guardian_id)
            self._guardian_shares_verifications(guardian_id)

        # ROUND 4 - CHALLENGES (IF NECESSARY)
        # If a verification fails, the key owner can challenge
        # and request another guardian verify the backup was indeed valid
        # In this example, we make a fake failure.
        self._guardian_challenges(guardian_ids)

        # CREATE JOINT KEY
        # If all backups are verified, publish joint key
        self._publish_joint_key()

    def _guardian_generates_keys(
        self, guardian_id: GUARDIAN_ID, sequence_order: int
    ) -> None:
        """Guardian generates their keys"""

        # Create Election Key Pair
        election_key_pair = generate_election_key_pair(
            guardian_id, sequence_order, self.QUORUM
        )
        self.assertIsNotNone(election_key_pair)
        self.election_key_pairs[guardian_id] = election_key_pair

        # Create Auxiliary Key Pair
        auxiliary_key_pair = generate_rsa_auxiliary_key_pair(
            guardian_id, sequence_order
        )
        self.assertIsNotNone(auxiliary_key_pair)
        self.auxiliary_key_pairs[guardian_id] = auxiliary_key_pair

    def _guardian_share_keys(self, guardian_id: GUARDIAN_ID) -> None:
        """Guardian shares public keys"""
        auxiliary_key_pair = self.auxiliary_key_pairs[guardian_id]
        election_key_pair = self.election_key_pairs[guardian_id]
        key_set = PublicKeySet(election_key_pair.share(), auxiliary_key_pair.share())
        self.assertIsNotNone(key_set)
        self.guardian_keys[guardian_id] = key_set

    def _guardian_generates_backups(self, sender_id: str) -> None:
        """
        Guardian generates a partial key backup of
        all other guardian keys
        """

        backups = []
        for recipient_auxiliary_key in self.auxiliary_key_pairs.values():
            # Guardian skips themselves
            if recipient_auxiliary_key.owner_id is sender_id:
                continue

            senders_polynomial = self.election_key_pairs[sender_id].polynomial
            backup = generate_election_partial_key_backup(
                sender_id,
                senders_polynomial,
                recipient_auxiliary_key.share(),
                identity_auxiliary_encrypt,
            )
            backups.append(backup)
        self.sent_backups[sender_id] = backups

    def _guardian_shares_backups(self, sender_id: GUARDIAN_ID) -> None:
        """Mock round robin to demonstrate sharing of backups"""

        backups_to_send = self.sent_backups[sender_id]
        for backup in backups_to_send:
            received_backups = self.received_backups.get(backup.designated_id)
            if received_backups is None:
                received_backups = []
            received_backups.append(backup)
            self.received_backups[backup.designated_id] = received_backups

    def _guardian_verifies_backups(self, verifier_id: str) -> None:
        """Guardian verifies the backups they have received"""

        verifications = []

        for backup in self.received_backups[verifier_id]:
            owner_public_key = self.election_key_pairs[backup.owner_id].share()
            verification = verify_election_partial_key_backup(
                verifier_id,
                backup,
                owner_public_key,
                self.auxiliary_key_pairs[verifier_id],
                identity_auxiliary_encrypt,
            )
            verifications.append(verification)
        self.sent_verifications[verifier_id] = verifications

    def _guardian_shares_verifications(self, verifier_id: str) -> None:
        """Mock round robin to demonstrate sharing of verifications"""

        verifications_to_send = self.sent_verifications[verifier_id]
        for verification in verifications_to_send:
            received_verifications = self.received_verifications.get(
                verification.owner_id
            )
            if received_verifications is None:
                received_verifications = []
            received_verifications.append(verification)
            self.received_verifications[verification.owner_id] = received_verifications

    def _guardian_checks_returned_verifications(
        self, key_owner_id: GUARDIAN_ID
    ) -> None:
        """
        Guardian checks that all backups have been
        verified sucessfully
        """

        verifications = self.received_verifications[key_owner_id]
        for verification in verifications:
            self.assertTrue(verification.verified)

    def _guardian_challenges(self, guardian_ids: List[GUARDIAN_ID]):
        key_owner_id = guardian_ids[0]
        original_verification = self.received_verifications[key_owner_id][0]
        failed_verification = ElectionPartialKeyVerification(
            original_verification.owner_id,
            original_verification.designated_id,
            original_verification.verifier_id,
            False,
        )
        designated_id = original_verification.designated_id

        # If backup failed to be verified
        self.assertFalse(failed_verification.verified)

        # Key Owner generate challenge
        designated_backup = [
            backup
            for backup in self.sent_backups[key_owner_id]
            if backup.designated_id == designated_id
        ][0]
        self.assertIsNotNone(designated_backup)
        election_key_pair = self.election_key_pairs[key_owner_id]
        challenge = generate_election_partial_key_challenge(
            designated_backup, election_key_pair.polynomial
        )

        # Get a mediator to verify who is not the owner or originally designated guardian who previously verified
        new_verifier_id = "mediator_id"

        # New verifier verifies challenge
        verification = verify_election_partial_key_challenge(
            new_verifier_id,
            challenge,
        )
        self.assertIsNotNone(verification)
        self.assertNotEqual(key_owner_id, verification.verifier_id)
        self.assertNotEqual(designated_id, verification.verifier_id)
        self.assertTrue(verification.verified)

        self.received_verifications[key_owner_id][0] = verification

    def _publish_joint_key(self) -> None:
        guardian_public_keys = [
            keys.share() for keys in self.election_key_pairs.values()
        ]
        election_joint_key = combine_election_public_keys(guardian_public_keys)
        self.assertIsNotNone(election_joint_key)
