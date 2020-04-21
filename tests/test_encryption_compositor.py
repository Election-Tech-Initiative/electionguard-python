import unittest
from datetime import datetime

from electionguard.encryption_compositor import (
    contest_from,
    encrypt_ballot,
    encrypt_contest,
    encrypt_selection,
    selection_from
)

from electionguard.ballot import (
    PlaintextBallot,
    PlaintextBallotContest,
    PlaintextBallotSelection,
    CyphertextBallotSelection
)

from electionguard.election import (
    BallotStyle,
    CyphertextElection,
    Election,
    ElectionType,
    GeopoliticalUnit,
    Candidate,
    Party,
    ContestDescription,
    SelectionDescription,
    ReportingUnitType,
    VoteVariationType
)

from electionguard.elgamal import (
    ElGamalKeyPair,
    elgamal_keypair_from_secret,
)
from electionguard.group import (
    ElementModQ,
    ONE_MOD_Q,
    int_to_q,
    add_q,
    unwrap_optional,
    Q,
    TWO_MOD_P,
    mult_p,
)

from electionguardtest.election_factory import ElectionFactory

from secrets import randbelow

class TestEncryptionCompositor(unittest.TestCase):

    def test_encrypt_selection_succeeds(self):

        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        nonce = randbelow(Q)
        metadata = SelectionDescription("some-selection-object-id", "some-candidate-id", 1)
        hash_context = metadata.crypto_hash()

        subject = selection_from(metadata)
        self.assertTrue(subject.is_valid(metadata.object_id))

        # Act
        result = encrypt_selection(subject, metadata, keypair.public_key, nonce)

        # Assert
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.message)
        self.assertTrue(result.is_valid_encryption(hash_context, keypair.public_key))

    def test_encrypt_contest_referendum_succeeds(self):

        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        nonce = randbelow(Q)
        metadata = ContestDescription("some-contest-object-id", "some-electoral-district-id", 0, VoteVariationType.one_of_m, 1, 1)
        metadata.ballot_selections = [
            SelectionDescription("some-object-id-affirmative", "some-candidate-id-affirmative", 0),
            SelectionDescription("some-object-id-negative", "some-candidate-id-negative", 1),
        ]
        metadata.votes_allowed = 1
        hash_context = metadata.crypto_hash()

        subject = contest_from(metadata)
        self.assertTrue(subject.is_valid(
            metadata.object_id,
            len(metadata.ballot_selections),
            metadata.number_elected,
            metadata.votes_allowed
        ))

        # Act
        result = encrypt_contest(subject, metadata, keypair.public_key, nonce)

        # Assert
        self.assertIsNotNone(result)
        self.assertTrue(result.is_valid_encryption(hash_context, keypair.public_key))

    def test_encrypt_ballot_simple_succeeds(self):

        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        generator = ElectionFactory()
        metadata = generator.get_fake_election()
        encryption_context = CyphertextElection(1, 1, metadata.crypto_hash())
        
        encryption_context.set_crypto_context(keypair.public_key)

        subject = generator.get_fake_ballot(metadata)
        self.assertTrue(subject.is_valid(metadata.ballot_styles[0].object_id))

        # Act
        result = encrypt_ballot(subject, metadata, encryption_context)

        # Assert
        self.assertIsNotNone(result)
        self.assertTrue(result.is_valid_encryption(encryption_context.crypto_extended_base_hash, keypair.public_key))
