from unittest import TestCase

from electionguard.data_store import DataStore
from electionguard.key_ceremony import (
    AuxiliaryPublicKey,
    ElectionPublicKey,
    generate_elgamal_auxiliary_key_pair,
    generate_election_key_pair,
    generate_election_partial_key_backup,
    verify_election_partial_key_backup,
    generate_election_partial_key_challenge,
    verify_election_partial_key_challenge,
    combine_election_public_keys,
)
from electionguard.types import GUARDIAN_ID

SENDER_GUARDIAN_ID = "Test Guardian 1"
RECIPIENT_GUARDIAN_ID = "Test Guardian 2"
ALTERNATE_VERIFIER_GUARDIAN_ID = "Test Guardian 3"
SENDER_SEQUENCE_ORDER = 1
RECIPIENT_SEQUENCE_ORDER = 2
AUXILIARY_PUBLIC_KEY = "Test Public Key"
NUMBER_OF_GUARDIANS = 5
QUORUM = 3


class TestKeyCeremony(TestCase):
    def test_generate_elgamal_auxiliary_key_pair(self):

        # Act
        auxiliary_key_pair = generate_elgamal_auxiliary_key_pair()

        # Assert
        self.assertIsNotNone(auxiliary_key_pair)
        self.assertIsNotNone(auxiliary_key_pair.public_key)
        self.assertIsNotNone(auxiliary_key_pair.secret_key)

    def test_generate_election_key_pair(self):
        # Act
        election_key_pair = generate_election_key_pair(NUMBER_OF_GUARDIANS)

        # Assert
        self.assertIsNotNone(election_key_pair)
        self.assertIsNotNone(election_key_pair.key_pair.public_key)
        self.assertIsNotNone(election_key_pair.key_pair.secret_key)
        self.assertIsNotNone(election_key_pair.polynomial)
        self.assertTrue(election_key_pair.proof.is_valid())
        for proof in election_key_pair.polynomial.coefficient_proofs:
            self.assertTrue(proof.is_valid())

    def test_generate_election_partial_key_backup(self):
        # Arrange
        election_key_pair = generate_election_key_pair(QUORUM)
        auxiliary_public_key = AuxiliaryPublicKey(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER, AUXILIARY_PUBLIC_KEY
        )

        # Act
        backup = generate_election_partial_key_backup(
            SENDER_GUARDIAN_ID, election_key_pair.polynomial, auxiliary_public_key
        )

        # Assert
        self.assertIsNotNone(backup)
        self.assertEqual(backup.designated_id, RECIPIENT_GUARDIAN_ID)
        self.assertEqual(backup.designated_sequence_order, RECIPIENT_SEQUENCE_ORDER)
        self.assertIsNotNone(backup.encrypted_value)
        self.assertEqual(len(backup.coefficient_commitments), QUORUM)
        self.assertEqual(len(backup.coefficient_proofs), QUORUM)
        for proof in backup.coefficient_proofs:
            self.assertTrue(proof.is_valid())

    def test_verify_election_partial_key_backup(self):
        # Arrange
        recipient_auxiliary_key_pair = generate_elgamal_auxiliary_key_pair()
        sender_election_key_pair = generate_election_key_pair(QUORUM)
        recipient_auxiliary_public_key = AuxiliaryPublicKey(
            RECIPIENT_GUARDIAN_ID,
            RECIPIENT_SEQUENCE_ORDER,
            recipient_auxiliary_key_pair.public_key,
        )
        partial_key_backup = generate_election_partial_key_backup(
            SENDER_GUARDIAN_ID,
            sender_election_key_pair.polynomial,
            recipient_auxiliary_public_key,
        )

        # Act
        verification = verify_election_partial_key_backup(
            RECIPIENT_GUARDIAN_ID, partial_key_backup, recipient_auxiliary_key_pair
        )

        # Assert
        self.assertIsNotNone(verification)
        self.assertEqual(verification.owner_id, SENDER_GUARDIAN_ID)
        self.assertEqual(verification.designated_id, RECIPIENT_GUARDIAN_ID)
        self.assertEqual(verification.verifier_id, RECIPIENT_GUARDIAN_ID)
        self.assertTrue(verification.verified)

    def test_generate_election_partial_key_challenge(self):
        # Arrange
        recipient_auxiliary_key_pair = generate_elgamal_auxiliary_key_pair()
        sender_election_key_pair = generate_election_key_pair(QUORUM)
        recipient_auxiliary_public_key = AuxiliaryPublicKey(
            RECIPIENT_GUARDIAN_ID,
            RECIPIENT_SEQUENCE_ORDER,
            recipient_auxiliary_key_pair.public_key,
        )
        partial_key_backup = generate_election_partial_key_backup(
            SENDER_GUARDIAN_ID,
            sender_election_key_pair.polynomial,
            recipient_auxiliary_public_key,
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

    def test_verify_election_partial_key_challenge(self):
        # Arrange
        recipient_auxiliary_key_pair = generate_elgamal_auxiliary_key_pair()
        sender_election_key_pair = generate_election_key_pair(QUORUM)
        recipient_auxiliary_public_key = AuxiliaryPublicKey(
            RECIPIENT_GUARDIAN_ID,
            RECIPIENT_SEQUENCE_ORDER,
            recipient_auxiliary_key_pair.public_key,
        )
        partial_key_backup = generate_election_partial_key_backup(
            SENDER_GUARDIAN_ID,
            sender_election_key_pair.polynomial,
            recipient_auxiliary_public_key,
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

    def test_combine_election_public_keys(self):
        # Arrange
        random_keypair = generate_election_key_pair(QUORUM)
        random_keypair_two = generate_election_key_pair(QUORUM)
        public_keys = DataStore[GUARDIAN_ID, ElectionPublicKey]()
        public_keys.set(
            RECIPIENT_GUARDIAN_ID,
            ElectionPublicKey(
                RECIPIENT_GUARDIAN_ID,
                random_keypair.proof,
                random_keypair.key_pair.public_key,
            ),
        )
        public_keys.set(
            SENDER_GUARDIAN_ID,
            ElectionPublicKey(
                SENDER_GUARDIAN_ID,
                random_keypair_two.proof,
                random_keypair_two.key_pair.public_key,
            ),
        )

        # Act
        joint_key = combine_election_public_keys(public_keys)

        # Assert
        self.assertIsNotNone(joint_key)
        self.assertNotEqual(joint_key, random_keypair.key_pair.public_key)
        self.assertNotEqual(joint_key, random_keypair_two.key_pair.public_key)
