# pylint: disable=too-many-public-methods

from tests.base_test_case import BaseTestCase

from electionguard.guardian import Guardian

from electionguard_tools.helpers.identity_encrypt import (
    identity_auxiliary_decrypt,
    identity_auxiliary_encrypt,
)

SENDER_GUARDIAN_ID = "Test Guardian 1"
RECIPIENT_GUARDIAN_ID = "Test Guardian 2"
ALTERNATE_VERIFIER_ID = "Test Verifier"
SENDER_SEQUENCE_ORDER = 1
RECIPIENT_SEQUENCE_ORDER = 2
ALTERNATE_VERIFIER_SEQUENCE_ORDER = 3
AUXILIARY_PUBLIC_KEY = "Test Public Key"
ELECTION_PUBLIC_KEY = ""
NUMBER_OF_GUARDIANS = 2
QUORUM = 2


class TestGuardian(BaseTestCase):
    """Guardian tests"""

    def test_reset(self):
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        expected_number_of_guardians = 10
        expected_quorum = 4

        # Act
        guardian.reset(expected_number_of_guardians, expected_quorum)

        # Assert
        self.assertEqual(
            expected_number_of_guardians, guardian.ceremony_details.number_of_guardians
        )
        self.assertEqual(expected_quorum, guardian.ceremony_details.quorum)

    def test_set_ceremony_details(self):
        # Arrange
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        expected_number_of_guardians = 10
        expected_quorum = 4

        # Act
        guardian.set_ceremony_details(expected_number_of_guardians, expected_quorum)

        # Assert
        self.assertEqual(
            expected_number_of_guardians, guardian.ceremony_details.number_of_guardians
        )
        self.assertEqual(expected_quorum, guardian.ceremony_details.quorum)

    def test_share_public_keys(self):
        # Arrange
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )

        # Act
        public_keys = guardian.share_public_keys()

        # Assert
        self.assertIsNotNone(public_keys)
        self.assertIsNotNone(public_keys.auxiliary)
        self.assertIsNotNone(public_keys.election)
        self.assertEqual(public_keys.election.owner_id, SENDER_GUARDIAN_ID)
        self.assertEqual(public_keys.auxiliary.owner_id, SENDER_GUARDIAN_ID)
        self.assertEqual(public_keys.election.sequence_order, SENDER_SEQUENCE_ORDER)
        self.assertEqual(public_keys.auxiliary.sequence_order, SENDER_SEQUENCE_ORDER)
        for proof in public_keys.election.coefficient_proofs:
            self.assertTrue(proof.is_valid())

    def test_save_guardian_public_keys(self):
        # Arrange
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        public_keys = other_guardian.share_public_keys()

        # Act
        guardian.save_guardian_public_keys(public_keys)

        # Assert
        self.assertTrue(guardian.all_auxiliary_public_keys_received())
        self.assertTrue(guardian.all_public_keys_received())

    def test_all_public_keys_received(self):
        # Arrange
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        public_keys = other_guardian.share_public_keys()

        # Act
        self.assertFalse(guardian.all_public_keys_received())
        guardian.save_guardian_public_keys(public_keys)

        # Assert
        self.assertTrue(guardian.all_public_keys_received())

    def test_generate_auxiliary_key_pair(self):
        # Arrange
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        first_public_key = guardian.share_auxiliary_public_key()

        # Act
        guardian.generate_auxiliary_key_pair()
        second_public_key = guardian.share_auxiliary_public_key()

        # Assert
        self.assertIsNotNone(second_public_key)
        self.assertIsNotNone(second_public_key.key)
        self.assertNotEqual(first_public_key.key, second_public_key.key)

    def test_share_auxiliary_public_key(self):
        # Arrange
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )

        # Act
        public_key = guardian.share_auxiliary_public_key()

        # Assert
        self.assertIsNotNone(public_key)
        self.assertIsNotNone(public_key.key)
        self.assertEqual(public_key.owner_id, SENDER_GUARDIAN_ID)
        self.assertEqual(public_key.sequence_order, SENDER_SEQUENCE_ORDER)

    def test_save_auxiliary_public_key(self):
        # Arrange
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        public_key = other_guardian.share_auxiliary_public_key()

        # Act
        guardian.save_auxiliary_public_key(public_key)

        # Assert
        self.assertTrue(guardian.all_auxiliary_public_keys_received())

    def test_all_auxiliary_public_keys_received(self):
        # Arrange
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        public_key = other_guardian.share_auxiliary_public_key()

        # Act
        self.assertFalse(guardian.all_auxiliary_public_keys_received())
        guardian.save_auxiliary_public_key(public_key)

        # Assert
        self.assertTrue(guardian.all_auxiliary_public_keys_received())

    def test_generate_election_key_pair(self):
        # Arrange
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        first_public_key = guardian.share_election_public_key()

        # Act
        guardian.generate_election_key_pair()
        second_public_key = guardian.share_election_public_key()

        # Assert
        self.assertIsNotNone(second_public_key)
        self.assertIsNotNone(second_public_key.key)
        self.assertNotEqual(first_public_key.key, second_public_key.key)

    def test_share_election_public_key(self):
        # Arrange
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )

        # Act
        public_key = guardian.share_election_public_key()

        # Assert
        self.assertIsNotNone(public_key)
        self.assertIsNotNone(public_key.key)
        self.assertEqual(public_key.owner_id, SENDER_GUARDIAN_ID)
        for proof in public_key.coefficient_proofs:
            self.assertTrue(proof.is_valid())

    def test_save_election_public_key(self):
        # Arrange
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        public_key = other_guardian.share_election_public_key()

        # Act
        guardian.save_election_public_key(public_key)

        # Assert
        self.assertTrue(guardian.all_election_public_keys_received())

    def test_all_election_public_keys_received(self):
        # Arrange
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        public_key = other_guardian.share_election_public_key()

        # Act
        self.assertFalse(guardian.all_election_public_keys_received())
        guardian.save_election_public_key(public_key)

        # Assert
        self.assertTrue(guardian.all_election_public_keys_received())

    def test_generate_election_partial_key_backups(self):
        # Arrange
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )

        # Act
        empty_key_backup = guardian.share_election_partial_key_backup(
            RECIPIENT_GUARDIAN_ID
        )
        # Assert
        self.assertIsNone(empty_key_backup)

        # Act
        guardian.save_auxiliary_public_key(other_guardian.share_auxiliary_public_key())
        guardian.generate_election_partial_key_backups(identity_auxiliary_encrypt)
        key_backup = guardian.share_election_partial_key_backup(RECIPIENT_GUARDIAN_ID)

        # Assert
        self.assertIsNotNone(key_backup)
        self.assertIsNotNone(key_backup.encrypted_value)
        self.assertEqual(key_backup.owner_id, SENDER_GUARDIAN_ID)
        self.assertEqual(key_backup.designated_id, RECIPIENT_GUARDIAN_ID)

    def test_share_election_partial_key_backup(self):
        # Arrange
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )

        # Act
        guardian.save_auxiliary_public_key(other_guardian.share_auxiliary_public_key())
        guardian.generate_election_partial_key_backups(identity_auxiliary_encrypt)
        key_backup = guardian.share_election_partial_key_backup(RECIPIENT_GUARDIAN_ID)

        # Assert
        self.assertIsNotNone(key_backup)
        self.assertIsNotNone(key_backup.encrypted_value)
        self.assertEqual(key_backup.owner_id, SENDER_GUARDIAN_ID)
        self.assertEqual(key_backup.designated_id, RECIPIENT_GUARDIAN_ID)

    def test_save_election_partial_key_backup(self):
        # Arrange
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )

        # Act
        guardian.save_auxiliary_public_key(other_guardian.share_auxiliary_public_key())
        guardian.generate_election_partial_key_backups(identity_auxiliary_encrypt)
        key_backup = guardian.share_election_partial_key_backup(RECIPIENT_GUARDIAN_ID)
        other_guardian.save_election_partial_key_backup(key_backup)

        # Assert
        self.assertTrue(other_guardian.all_election_partial_key_backups_received())

    def test_all_election_partial_key_backups_received(self):
        # Arrange
        # Round 1
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        guardian.save_guardian_public_keys(other_guardian.share_public_keys())
        other_guardian.save_guardian_public_keys(guardian.share_public_keys())

        # Round 2
        guardian.generate_election_partial_key_backups(identity_auxiliary_encrypt)
        key_backup = guardian.share_election_partial_key_backup(RECIPIENT_GUARDIAN_ID)

        # Assert
        self.assertFalse(other_guardian.all_election_partial_key_backups_received())
        other_guardian.save_election_partial_key_backup(key_backup)
        self.assertTrue(other_guardian.all_election_partial_key_backups_received())

    def test_verify_election_partial_key_backup(self):
        # Arrange
        # Round 1
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        guardian.save_guardian_public_keys(other_guardian.share_public_keys())
        other_guardian.save_guardian_public_keys(guardian.share_public_keys())

        # Round 2
        guardian.generate_election_partial_key_backups(identity_auxiliary_encrypt)
        key_backup = guardian.share_election_partial_key_backup(RECIPIENT_GUARDIAN_ID)
        other_guardian.save_election_partial_key_backup(key_backup)

        # Act
        verification = other_guardian.verify_election_partial_key_backup(
            SENDER_GUARDIAN_ID, identity_auxiliary_decrypt
        )

        # Assert
        self.assertIsNotNone(verification)
        self.assertEqual(verification.owner_id, SENDER_GUARDIAN_ID)
        self.assertEqual(verification.designated_id, RECIPIENT_GUARDIAN_ID)
        self.assertEqual(verification.verifier_id, RECIPIENT_GUARDIAN_ID)
        self.assertTrue(verification.verified)

    def test_verify_election_partial_key_challenge(self):
        # Arrange
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        recipient_guardian = Guardian(
            RECIPIENT_GUARDIAN_ID,
            RECIPIENT_SEQUENCE_ORDER,
            NUMBER_OF_GUARDIANS,
            QUORUM,
        )
        alternate_verifier = Guardian(
            ALTERNATE_VERIFIER_ID,
            ALTERNATE_VERIFIER_SEQUENCE_ORDER,
            NUMBER_OF_GUARDIANS,
            QUORUM,
        )
        guardian.save_auxiliary_public_key(
            recipient_guardian.share_auxiliary_public_key()
        )
        guardian.generate_election_partial_key_backups(identity_auxiliary_encrypt)
        challenge = guardian.publish_election_backup_challenge(RECIPIENT_GUARDIAN_ID)

        # Act
        verification = alternate_verifier.verify_election_partial_key_challenge(
            challenge
        )

        # Assert
        self.assertIsNotNone(verification)
        self.assertEqual(verification.owner_id, SENDER_GUARDIAN_ID)
        self.assertEqual(verification.designated_id, RECIPIENT_GUARDIAN_ID)
        self.assertEqual(verification.verifier_id, ALTERNATE_VERIFIER_ID)
        self.assertTrue(verification.verified)

    def test_publish_election_backup_challenge(self):
        # Arrange
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        recipient_guardian = Guardian(
            RECIPIENT_GUARDIAN_ID,
            RECIPIENT_SEQUENCE_ORDER,
            NUMBER_OF_GUARDIANS,
            QUORUM,
        )

        guardian.save_auxiliary_public_key(
            recipient_guardian.share_auxiliary_public_key()
        )
        guardian.generate_election_partial_key_backups(identity_auxiliary_encrypt)

        # Act
        challenge = guardian.publish_election_backup_challenge(RECIPIENT_GUARDIAN_ID)

        # Assert
        self.assertIsNotNone(challenge)
        self.assertIsNotNone(challenge.value)
        self.assertEqual(challenge.owner_id, SENDER_GUARDIAN_ID)
        self.assertEqual(challenge.designated_id, RECIPIENT_GUARDIAN_ID)
        self.assertEqual(len(challenge.coefficient_commitments), QUORUM)
        self.assertEqual(len(challenge.coefficient_proofs), QUORUM)
        for proof in challenge.coefficient_proofs:
            proof.is_valid()

    def test_save_election_partial_key_verification(self):
        # Arrange
        # Round 1
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        guardian.save_guardian_public_keys(other_guardian.share_public_keys())
        other_guardian.save_guardian_public_keys(guardian.share_public_keys())

        # Round 2
        guardian.generate_election_partial_key_backups(identity_auxiliary_encrypt)
        key_backup = guardian.share_election_partial_key_backup(RECIPIENT_GUARDIAN_ID)
        other_guardian.save_election_partial_key_backup(key_backup)
        verification = other_guardian.verify_election_partial_key_backup(
            SENDER_GUARDIAN_ID, identity_auxiliary_decrypt
        )

        # Act
        guardian.save_election_partial_key_verification(verification)

        # Assert
        self.assertTrue(guardian.all_election_partial_key_backups_verified)

    def test_all_election_partial_key_backups_verified(self):
        # Arrange
        # Round 1
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        guardian.save_guardian_public_keys(other_guardian.share_public_keys())
        other_guardian.save_guardian_public_keys(guardian.share_public_keys())

        # Round 2
        guardian.generate_election_partial_key_backups(identity_auxiliary_encrypt)
        key_backup = guardian.share_election_partial_key_backup(RECIPIENT_GUARDIAN_ID)
        other_guardian.save_election_partial_key_backup(key_backup)
        verification = other_guardian.verify_election_partial_key_backup(
            SENDER_GUARDIAN_ID, identity_auxiliary_decrypt
        )
        guardian.save_election_partial_key_verification(verification)

        # Act
        all_saved = guardian.all_election_partial_key_backups_verified()

        # Assert
        self.assertTrue(all_saved)

    def test_publish_joint_key(self):
        # Arrange
        # Round 1
        guardian = Guardian(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        guardian.save_guardian_public_keys(other_guardian.share_public_keys())
        other_guardian.save_guardian_public_keys(guardian.share_public_keys())

        # Round 2
        guardian.generate_election_partial_key_backups(identity_auxiliary_encrypt)
        key_backup = guardian.share_election_partial_key_backup(RECIPIENT_GUARDIAN_ID)
        other_guardian.save_election_partial_key_backup(key_backup)
        verification = other_guardian.verify_election_partial_key_backup(
            SENDER_GUARDIAN_ID, identity_auxiliary_decrypt
        )

        # Act
        joint_key = guardian.publish_joint_key()

        # Assert
        self.assertIsNone(joint_key)

        # Act
        guardian.save_election_public_key(other_guardian.share_election_public_key())
        joint_key = guardian.publish_joint_key()

        # Assert
        self.assertIsNone(joint_key)

        # Act
        guardian.save_election_partial_key_verification(verification)
        joint_key = guardian.publish_joint_key()

        # Assert
        self.assertIsNotNone(joint_key)
        self.assertNotEqual(joint_key, guardian.share_election_public_key().key)
