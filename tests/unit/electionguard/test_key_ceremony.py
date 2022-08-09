import os
from unittest.mock import patch
from tests.base_test_case import BaseTestCase

from electionguard.constants import (
    PrimeOption,
)

from electionguard.key_ceremony import (
    generate_election_key_pair,
    generate_election_partial_key_backup,
    verify_election_partial_key_backup,
    generate_election_partial_key_challenge,
    verify_election_partial_key_challenge,
    combine_election_public_keys,
)

NUMBER_OF_GUARDIANS = 5
QUORUM = 3

SENDER_GUARDIAN_ID = "Test Guardian 1"
SENDER_SEQUENCE_ORDER = 1

RECIPIENT_GUARDIAN_ID = "Test Guardian 2"
RECIPIENT_SEQUENCE_ORDER = 2
RECIPIENT_KEY_PAIR = generate_election_key_pair(
    RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, QUORUM
)
RECIPIENT_KEY = RECIPIENT_KEY_PAIR.share()

ALTERNATE_VERIFIER_GUARDIAN_ID = "Test Guardian 3"


@patch.dict(os.environ, {"PRIME_OPTION": PrimeOption.Standard.value})
class TestKeyCeremony(BaseTestCase):
    """Key ceremony tests"""

    def test_generate_election_key_pair(self) -> None:
        # Act
        election_key_pair = generate_election_key_pair(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, QUORUM
        )

        # Assert
        self.assertIsNotNone(election_key_pair)
        self.assertIsNotNone(election_key_pair.key_pair.public_key)
        self.assertIsNotNone(election_key_pair.key_pair.secret_key)
        self.assertIsNotNone(election_key_pair.polynomial)

        self.assertEqual(len(election_key_pair.polynomial.coefficients), QUORUM)
        for coefficient in election_key_pair.polynomial.coefficients:
            self.assertTrue(coefficient.proof.is_valid())

    def test_generate_election_partial_key_backup(self) -> None:
        # Arrange
        election_key_pair = generate_election_key_pair(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, QUORUM
        )

        # Act
        backup = generate_election_partial_key_backup(
            SENDER_GUARDIAN_ID,
            election_key_pair.polynomial,
            RECIPIENT_KEY,
        )

        # Assert
        self.assertIsNotNone(backup)
        self.assertEqual(backup.designated_id, RECIPIENT_GUARDIAN_ID)
        self.assertEqual(backup.designated_sequence_order, RECIPIENT_SEQUENCE_ORDER)
        self.assertIsNotNone(backup.encrypted_coordinate)

    def test_encrypt_then_verify_coordinate(self) -> None:
        # Arrange
        sender_key_pair = generate_election_key_pair(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, QUORUM
        )

        # Act
        partial_key_backup = generate_election_partial_key_backup(
            SENDER_GUARDIAN_ID,
            sender_key_pair.polynomial,
            RECIPIENT_KEY,
        )
        verification = verify_election_partial_key_backup(
            RECIPIENT_GUARDIAN_ID,
            partial_key_backup,
            sender_key_pair.share(),
            RECIPIENT_KEY_PAIR,
        )

        # Assert
        self.assertTrue(verification.verified)

    def test_verify_election_partial_key_backup(self) -> None:
        # Arrange
        sender_election_key_pair = generate_election_key_pair(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, QUORUM
        )

        partial_key_backup = generate_election_partial_key_backup(
            SENDER_GUARDIAN_ID,
            sender_election_key_pair.polynomial,
            RECIPIENT_KEY,
        )

        # Act
        verification = verify_election_partial_key_backup(
            RECIPIENT_GUARDIAN_ID,
            partial_key_backup,
            sender_election_key_pair.share(),
            RECIPIENT_KEY_PAIR,
        )

        # Assert
        self.assertIsNotNone(verification)
        self.assertEqual(verification.owner_id, SENDER_GUARDIAN_ID)
        self.assertEqual(verification.designated_id, RECIPIENT_GUARDIAN_ID)
        self.assertEqual(verification.verifier_id, RECIPIENT_GUARDIAN_ID)
        self.assertTrue(verification.verified)

    def test_generate_election_partial_key_challenge(self) -> None:
        # Arrange
        sender_election_key_pair = generate_election_key_pair(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, QUORUM
        )
        partial_key_backup = generate_election_partial_key_backup(
            SENDER_GUARDIAN_ID,
            sender_election_key_pair.polynomial,
            RECIPIENT_KEY,
        )

        # Act
        challenge = generate_election_partial_key_challenge(
            partial_key_backup, sender_election_key_pair.polynomial
        )

        # Assert
        self.assertIsNotNone(challenge)
        self.assertEqual(challenge.designated_id, RECIPIENT_GUARDIAN_ID)
        self.assertEqual(challenge.designated_sequence_order, RECIPIENT_SEQUENCE_ORDER)
        self.assertIsNotNone(challenge.value)
        self.assertEqual(len(challenge.coefficient_commitments), QUORUM)
        self.assertEqual(len(challenge.coefficient_proofs), QUORUM)
        for proof in challenge.coefficient_proofs:
            self.assertTrue(proof.is_valid())

    def test_verify_election_partial_key_challenge(self) -> None:
        # Arrange
        sender_election_key_pair = generate_election_key_pair(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, QUORUM
        )
        partial_key_backup = generate_election_partial_key_backup(
            SENDER_GUARDIAN_ID,
            sender_election_key_pair.polynomial,
            RECIPIENT_KEY,
        )
        challenge = generate_election_partial_key_challenge(
            partial_key_backup, sender_election_key_pair.polynomial
        )

        # Act
        verification = verify_election_partial_key_challenge(
            ALTERNATE_VERIFIER_GUARDIAN_ID, challenge
        )

        # Assert
        self.assertIsNotNone(verification)
        self.assertEqual(verification.owner_id, SENDER_GUARDIAN_ID)
        self.assertEqual(verification.designated_id, RECIPIENT_GUARDIAN_ID)
        self.assertEqual(verification.verifier_id, ALTERNATE_VERIFIER_GUARDIAN_ID)
        self.assertTrue(verification.verified)

    def test_combine_election_public_keys(self) -> None:
        # Arrange
        random_key = generate_election_key_pair(
            RECIPIENT_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, QUORUM
        ).share()
        random_key_two = generate_election_key_pair(
            SENDER_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, QUORUM
        ).share()

        # Act
        joint_key = combine_election_public_keys([random_key, random_key_two])

        # Assert
        self.assertIsNotNone(joint_key)
        self.assertNotEqual(joint_key.joint_public_key, random_key.key)
        self.assertNotEqual(joint_key.joint_public_key, random_key_two.key)
