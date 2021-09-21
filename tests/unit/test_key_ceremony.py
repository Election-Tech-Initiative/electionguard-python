from tests.base_test_case import BaseTestCase

from electionguard.key_ceremony import (
    AuxiliaryPublicKey,
    generate_election_key_pair,
    generate_rsa_auxiliary_key_pair,
    generate_election_partial_key_backup,
    verify_election_partial_key_backup,
    generate_election_partial_key_challenge,
    verify_election_partial_key_challenge,
    combine_election_public_keys,
)
from electionguard_tools.helpers.identity_encrypt import (
    identity_auxiliary_decrypt,
    identity_auxiliary_encrypt,
)

SENDER_GUARDIAN_ID = "Test Guardian 1"
RECIPIENT_GUARDIAN_ID = "Test Guardian 2"
ALTERNATE_VERIFIER_GUARDIAN_ID = "Test Guardian 3"
SENDER_SEQUENCE_ORDER = 1
RECIPIENT_SEQUENCE_ORDER = 2
NUMBER_OF_GUARDIANS = 5
QUORUM = 3


class TestKeyCeremony(BaseTestCase):
    """Key ceremony tests"""

    def test_generate_rsa_auxiliary_key_pair(self):

        # Act
        auxiliary_key_pair = generate_rsa_auxiliary_key_pair(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER
        )

        # Assert
        self.assertIsNotNone(auxiliary_key_pair)
        self.assertIsNotNone(auxiliary_key_pair.public_key)
        self.assertIsNotNone(auxiliary_key_pair.secret_key)

    def test_generate_election_key_pair(self):
        # Act
        election_key_pair = generate_election_key_pair(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, QUORUM
        )

        # Assert
        self.assertIsNotNone(election_key_pair)
        self.assertIsNotNone(election_key_pair.key_pair.public_key)
        self.assertIsNotNone(election_key_pair.key_pair.secret_key)
        self.assertIsNotNone(election_key_pair.polynomial)
        self.assertEqual(
            len(election_key_pair.polynomial.coefficient_commitments), QUORUM
        )
        self.assertEqual(len(election_key_pair.polynomial.coefficient_proofs), QUORUM)
        for proof in election_key_pair.polynomial.coefficient_proofs:
            self.assertTrue(proof.is_valid())

    def test_generate_election_partial_key_backup(self):
        # Arrange
        election_key_pair = generate_election_key_pair(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, QUORUM
        )
        auxiliary_key_pair = generate_rsa_auxiliary_key_pair(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER
        )
        auxiliary_public_key = AuxiliaryPublicKey(
            RECIPIENT_GUARDIAN_ID,
            RECIPIENT_SEQUENCE_ORDER,
            auxiliary_key_pair.public_key,
        )

        # Act
        backup = generate_election_partial_key_backup(
            SENDER_GUARDIAN_ID,
            election_key_pair.polynomial,
            auxiliary_public_key,
            identity_auxiliary_encrypt,
        )

        # Assert
        self.assertIsNotNone(backup)
        self.assertEqual(backup.designated_id, RECIPIENT_GUARDIAN_ID)
        self.assertEqual(backup.designated_sequence_order, RECIPIENT_SEQUENCE_ORDER)
        self.assertIsNotNone(backup.encrypted_value)

    def test_verify_election_partial_key_backup(self):
        # Arrange
        recipient_auxiliary_key_pair = generate_rsa_auxiliary_key_pair(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER
        )
        sender_election_key_pair = generate_election_key_pair(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, QUORUM
        )
        recipient_auxiliary_public_key = AuxiliaryPublicKey(
            RECIPIENT_GUARDIAN_ID,
            RECIPIENT_SEQUENCE_ORDER,
            recipient_auxiliary_key_pair.public_key,
        )
        partial_key_backup = generate_election_partial_key_backup(
            SENDER_GUARDIAN_ID,
            sender_election_key_pair.polynomial,
            recipient_auxiliary_public_key,
            identity_auxiliary_encrypt,
        )

        # Act
        verification = verify_election_partial_key_backup(
            RECIPIENT_GUARDIAN_ID,
            partial_key_backup,
            sender_election_key_pair.share(),
            recipient_auxiliary_key_pair,
            identity_auxiliary_decrypt,
        )

        # Assert
        self.assertIsNotNone(verification)
        self.assertEqual(verification.owner_id, SENDER_GUARDIAN_ID)
        self.assertEqual(verification.designated_id, RECIPIENT_GUARDIAN_ID)
        self.assertEqual(verification.verifier_id, RECIPIENT_GUARDIAN_ID)
        self.assertTrue(verification.verified)

    def test_generate_election_partial_key_challenge(self):
        # Arrange
        recipient_auxiliary_key_pair = generate_rsa_auxiliary_key_pair(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER
        )
        sender_election_key_pair = generate_election_key_pair(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, QUORUM
        )
        recipient_auxiliary_public_key = AuxiliaryPublicKey(
            RECIPIENT_GUARDIAN_ID,
            RECIPIENT_SEQUENCE_ORDER,
            recipient_auxiliary_key_pair.public_key,
        )
        partial_key_backup = generate_election_partial_key_backup(
            SENDER_GUARDIAN_ID,
            sender_election_key_pair.polynomial,
            recipient_auxiliary_public_key,
            identity_auxiliary_encrypt,
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
        recipient_auxiliary_key_pair = generate_rsa_auxiliary_key_pair(
            RECIPIENT_GUARDIAN_ID, RECIPIENT_SEQUENCE_ORDER
        )
        sender_election_key_pair = generate_election_key_pair(
            SENDER_GUARDIAN_ID, SENDER_SEQUENCE_ORDER, QUORUM
        )
        recipient_auxiliary_public_key = AuxiliaryPublicKey(
            RECIPIENT_GUARDIAN_ID,
            RECIPIENT_SEQUENCE_ORDER,
            recipient_auxiliary_key_pair.public_key,
        )
        partial_key_backup = generate_election_partial_key_backup(
            SENDER_GUARDIAN_ID,
            sender_election_key_pair.polynomial,
            recipient_auxiliary_public_key,
            identity_auxiliary_encrypt,
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
