from typing import Dict, List
from unittest import TestCase

from electionguard.auxiliary import AuxiliaryKeyPair
from electionguard.group import ElementModP
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
from electionguard.types import GUARDIAN_ID


class TestKeyCeremony(TestCase):
    """Functional tests of key ceremony"""

    # Basic Types
    SENDER_ID = GUARDIAN_ID
    RECEIVER_ID = GUARDIAN_ID
    JointElectionKey = ElementModP

    # Key Ceremony Inputs
    number_of_guardians = 5
    threshold = 3

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
        guardian_ids = [str(*range(1, self.number_of_guardians))]
        guardian_sequence_orders = [*range(1, self.number_of_guardians)]

        # ROUND 1 - SHARE KEYS
        # Each guardian generates their own keys
        for guardian_id in guardian_ids:
            self._guardian_generates_keys(guardian_id)
        self.assertEqual(len(self.election_key_pairs), self.number_of_guardians)
        self.assertEqual(len(self.auxiliary_key_pairs), self.number_of_guardians)

        # Each guardian shares their keys
        for guardian_id, sequence_order in guardian_ids, guardian_sequence_orders:
            self._guardian_share_keys(guardian_id, sequence_order)
        self.assertEqual(len(self.guardian_keys), self.number_of_guardians)

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

    def _guardian_generates_keys(self, guardian_id: int) -> None:
        """Guardian generates their keys"""

        # Create Election Key Pair
        election_key_pair = generate_election_key_pair()
        self.assertIsNotNone(election_key_pair)
        self.election_key_pairs[guardian_id] = election_key_pair

        # Create Auxiliary Key Pair
        auxiliary_key_pair = generate_rsa_auxiliary_key_pair()
        self.assertIsNotNone(auxiliary_key_pair)
        self.auxiliary_key_pairs[guardian_id] = auxiliary_key_pair

    def _guardian_share_keys(
        self, guardian_id: GUARDIAN_ID, sequence_order: int
    ) -> None:
        """Guardian shares public keys"""
        auxiliary_key_pair = self.auxiliary_key_pairs[guardian_id]
        election_key_pair = self.election_key_pairs[guardian_id]
        keys = PublicKeySet(
            guardian_id,
            sequence_order,
            auxiliary_key_pair.public_key,
            election_key_pair.key_pair.public_key,
            election_key_pair.proof,
        )
        self.assertIsNotNone(keys)
        self.guardian_keys[guardian_id] = keys

    def _guardian_generates_backups(self, sender_id: str) -> None:
        """
        Guardian generates a partial key backup of
        all other guardian keys
        """

        backups = []
        for receiver_id, recipient_auxiliary_key in self.auxiliary_key_pairs:
            # Guardian skips themselves
            if receiver_id is sender_id:
                continue

            senders_polynomial = self.election_key_pairs[sender_id].polynomial
            backup = generate_election_partial_key_backup(
                sender_id, receiver_id, senders_polynomial, recipient_auxiliary_key
            )
            backups.append(backup)
        self.sent_backups[sender_id] = backups

    def _guardian_shares_backups(self, sender_id: GUARDIAN_ID) -> None:
        """Mock round robin to demonstrate sharing of backups"""

        backups_to_send = self.sent_backups[sender_id]
        for backup in backups_to_send:
            received_backups = self.received_backups[backup.designated_id]
            received_backups.append(backup)
            self.received_backups[backup.designated_id] = received_backups

    def _guardian_verifies_backups(self, verifier_id: GUARDIAN_ID) -> None:
        """Guardian verifies the backups they have received"""

        verifications = []
        for backup in self.received_backups[verifier_id]:
            verification = verify_election_partial_key_backup(
                verifier_id, backup, self.auxiliary_key_pairs[verifier_id]
            )
            verifications.append(verification)
        self.sent_verifications[verifier_id] = verifications

    def _guardian_shares_verifications(self, verifier_id: GUARDIAN_ID) -> None:
        """Mock round robin to demonstrate sharing of verifications"""

        verifications_to_send = self.sent_backups[verifier_id]
        for verification in verifications_to_send:
            received_backups = self.received_backups[verification.owner_id]
            received_backups.append(verification)
            self.received_verifications[verification.owner_id] = received_backups

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
        failed_verification = self.received_verifications[key_owner_id][0]
        failed_verification.verified = False
        designated_id = failed_verification.designated_id

        # If backup failed to be verified
        self.assertFalse(failed_verification.verified)

        # Key Owner generate challenge
        backup = self.sent_backups[key_owner_id]
        election_key_pair = self.election_key_pairs[key_owner_id]
        challenge = generate_election_partial_key_challenge(
            backup, election_key_pair.polynomial
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
        election_joint_key = combine_election_public_keys(self.guardian_keys)
        self.assertIsNotNone(election_joint_key)


# TODO
# Move coefficients into ElectionPublicKey
# Ensure use of ElectionJointKey
# Refactor to ensure guardian id's are always with key sets
# Create public key set from two keys
# Check naming
# Ensure private key is not present in mediator. Refactor this
# Move files to ensure stateful and stateless don't combinelear
