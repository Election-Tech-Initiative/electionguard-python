# pylint: disable=too-many-public-methods


from tests.base_test_case import BaseTestCase

from electionguard.guardian import Guardian

NUMBER_OF_GUARDIANS = 2
QUORUM = 2

SENDER_GUARDIAN_ID = "Test Guardian 1"
SENDER_SEQUENCE_ORDER = 1

RECIPIENT_GUARDIAN_ID = "Test Guardian 2"
RECIPIENT_SEQUENCE_ORDER = 2

ALTERNATE_VERIFIER_ID = "Test Verifier"
ALTERNATE_VERIFIER_SEQUENCE_ORDER = 3

ELECTION_PUBLIC_KEY = ""


class TestGuardian(BaseTestCase):
    """Guardian tests"""

    def test_import_from_guardian_private_record(self) -> None:
        # Arrange
        guardian_expected = Guardian.from_nonce(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        private_guardian_record = guardian_expected.export_private_data()

        # Act
        guardian_actual = Guardian.from_private_record(
            private_guardian_record, NUMBER_OF_GUARDIANS, QUORUM
        )

        # Assert
        # pylint: disable=protected-access
        self.assertEqual(
            guardian_actual._election_keys, guardian_expected._election_keys
        )
        self.assertEqual(
            guardian_actual._guardian_election_public_keys,
            guardian_expected._guardian_election_public_keys,
        )
        self.assertEqual(
            guardian_actual._guardian_election_partial_key_backups,
            guardian_expected._guardian_election_partial_key_backups,
        )

    def test_set_ceremony_details(self) -> None:
        # Arrange
        guardian = Guardian.from_nonce(
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

    def test_share_key(self) -> None:
        # Arrange
        guardian = Guardian.from_nonce(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )

        # Act
        key = guardian.share_key()

        # Assert
        self.assertIsNotNone(key)
        self.assertIsNotNone(key.key)
        self.assertEqual(key.owner_id, SENDER_GUARDIAN_ID)
        for proof in key.coefficient_proofs:
            self.assertTrue(proof.is_valid())

    def test_save_guardian_key(self) -> None:
        # Arrange
        guardian = Guardian.from_nonce(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian.from_nonce(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        key = other_guardian.share_key()

        # Act
        guardian.save_guardian_key(key)

        # Assert
        self.assertTrue(guardian.all_guardian_keys_received())

    def test_all_guardian_keys_received(self) -> None:
        # Arrange
        guardian = Guardian.from_nonce(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian.from_nonce(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        key = other_guardian.share_key()

        # Act
        self.assertFalse(guardian.all_guardian_keys_received())
        guardian.save_guardian_key(key)

        # Assert
        self.assertTrue(guardian.all_guardian_keys_received())

    def test_share_backups(self) -> None:
        # Arrange
        guardian = Guardian.from_nonce(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian.from_nonce(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        guardian.save_guardian_key(other_guardian.share_key())

        # Act
        empty_key_backup = guardian.share_election_partial_key_backup(other_guardian.id)

        # Assert
        self.assertIsNone(empty_key_backup)

        # Act
        guardian.generate_election_partial_key_backups()
        key_backup = guardian.share_election_partial_key_backup(other_guardian.id)

        # Assert
        self.assertIsNotNone(key_backup)
        self.assertIsNotNone(key_backup.encrypted_coordinate)
        self.assertEqual(key_backup.owner_id, guardian.id)
        self.assertEqual(key_backup.designated_id, other_guardian.id)

    def test_save_election_partial_key_backup(self) -> None:
        # Arrange
        guardian = Guardian.from_nonce(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian.from_nonce(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        guardian.save_guardian_key(other_guardian.share_key())
        guardian.generate_election_partial_key_backups()
        key_backup = guardian.share_election_partial_key_backup(other_guardian.id)

        # Act
        other_guardian.save_election_partial_key_backup(key_backup)

        # Assert
        self.assertTrue(other_guardian.all_election_partial_key_backups_received())

    def test_all_election_partial_key_backups_received(self) -> None:
        # Arrange
        # Round 1
        guardian = Guardian.from_nonce(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian.from_nonce(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        guardian.save_guardian_key(other_guardian.share_key())
        other_guardian.save_guardian_key(guardian.share_key())

        # Round 2
        guardian.generate_election_partial_key_backups()
        key_backup = guardian.share_election_partial_key_backup(other_guardian.id)

        # Assert
        self.assertFalse(other_guardian.all_election_partial_key_backups_received())
        other_guardian.save_election_partial_key_backup(key_backup)
        self.assertTrue(other_guardian.all_election_partial_key_backups_received())

    def test_verify_election_partial_key_backup(self) -> None:
        # Arrange
        # Round 1
        guardian = Guardian.from_nonce(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian.from_nonce(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        guardian.save_guardian_key(other_guardian.share_key())
        other_guardian.save_guardian_key(guardian.share_key())

        # Round 2
        guardian.generate_election_partial_key_backups()
        key_backup = guardian.share_election_partial_key_backup(other_guardian.id)
        other_guardian.save_election_partial_key_backup(key_backup)

        # Act
        verification = other_guardian.verify_election_partial_key_backup(
            guardian.id,
        )

        # Assert
        self.assertIsNotNone(verification)
        self.assertEqual(verification.owner_id, guardian.id)
        self.assertEqual(verification.designated_id, other_guardian.id)
        self.assertEqual(verification.verifier_id, other_guardian.id)
        self.assertTrue(verification.verified)

    def test_verify_election_partial_key_challenge(self) -> None:
        # Arrange
        guardian = Guardian.from_nonce(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian.from_nonce(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        alternate_verifier = Guardian.from_nonce(
            ALTERNATE_VERIFIER_ID,
            ALTERNATE_VERIFIER_SEQUENCE_ORDER,
            NUMBER_OF_GUARDIANS,
            QUORUM,
        )
        guardian.save_guardian_key(other_guardian.share_key())
        guardian.generate_election_partial_key_backups()
        challenge = guardian.publish_election_backup_challenge(other_guardian.id)

        # Act
        verification = alternate_verifier.verify_election_partial_key_challenge(
            challenge
        )

        # Assert
        self.assertIsNotNone(verification)
        self.assertEqual(verification.owner_id, guardian.id)
        self.assertEqual(verification.designated_id, other_guardian.id)
        self.assertEqual(verification.verifier_id, alternate_verifier.id)
        self.assertTrue(verification.verified)

    def test_publish_election_backup_challenge(self) -> None:
        # Arrange
        guardian = Guardian.from_nonce(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian.from_nonce(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        guardian.save_guardian_key(other_guardian.share_key())
        guardian.generate_election_partial_key_backups()

        # Act
        challenge = guardian.publish_election_backup_challenge(other_guardian.id)

        # Assert
        self.assertIsNotNone(challenge)
        self.assertIsNotNone(challenge.value)
        self.assertEqual(challenge.owner_id, guardian.id)
        self.assertEqual(challenge.designated_id, other_guardian.id)
        self.assertEqual(len(challenge.coefficient_commitments), QUORUM)
        self.assertEqual(len(challenge.coefficient_proofs), QUORUM)
        for proof in challenge.coefficient_proofs:
            proof.is_valid()

    def test_save_election_partial_key_verification(self) -> None:
        # Arrange
        # Round 1
        guardian = Guardian.from_nonce(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian.from_nonce(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        guardian.save_guardian_key(other_guardian.share_key())
        other_guardian.save_guardian_key(guardian.share_key())

        # Round 2
        guardian.generate_election_partial_key_backups()
        key_backup = guardian.share_election_partial_key_backup(RECIPIENT_GUARDIAN_ID)
        other_guardian.save_election_partial_key_backup(key_backup)
        verification = other_guardian.verify_election_partial_key_backup(
            SENDER_GUARDIAN_ID,
        )

        # Act
        guardian.save_election_partial_key_verification(verification)

        # Assert
        self.assertTrue(guardian.all_election_partial_key_backups_verified)

    def test_all_election_partial_key_backups_verified(self) -> None:
        # Arrange
        # Round 1
        guardian = Guardian.from_nonce(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian.from_nonce(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        guardian.save_guardian_key(other_guardian.share_key())
        other_guardian.save_guardian_key(guardian.share_key())

        # Round 2
        guardian.generate_election_partial_key_backups()
        key_backup = guardian.share_election_partial_key_backup(other_guardian.id)
        other_guardian.save_election_partial_key_backup(key_backup)
        verification = other_guardian.verify_election_partial_key_backup(
            guardian.id,
        )
        guardian.save_election_partial_key_verification(verification)

        # Act
        all_saved = guardian.all_election_partial_key_backups_verified()

        # Assert
        self.assertTrue(all_saved)

    def test_publish_joint_key(self) -> None:
        # Arrange
        # Round 1
        guardian = Guardian.from_nonce(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        other_guardian = Guardian.from_nonce(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, NUMBER_OF_GUARDIANS, QUORUM
        )
        guardian.save_guardian_key(other_guardian.share_key())
        other_guardian.save_guardian_key(guardian.share_key())

        # Round 2
        guardian.generate_election_partial_key_backups()
        key_backup = guardian.share_election_partial_key_backup(other_guardian.id)
        other_guardian.save_election_partial_key_backup(key_backup)
        verification = other_guardian.verify_election_partial_key_backup(
            guardian.id,
        )

        # Act
        joint_key = guardian.publish_joint_key()

        # Assert
        self.assertIsNone(joint_key)

        # Act
        guardian.save_guardian_key(other_guardian.share_key())
        joint_key = guardian.publish_joint_key()

        # Assert
        self.assertIsNone(joint_key)

        # Act
        guardian.save_election_partial_key_verification(verification)
        joint_key = guardian.publish_joint_key()

        # Assert
        self.assertIsNotNone(joint_key)
        self.assertNotEqual(joint_key, guardian.share_key().key)
