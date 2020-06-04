import unittest

from electionguard.ballot import BallotBoxState
from electionguard.ballot_store import BallotStore

from electionguard.ballot_box import (
    BallotBox,
    cast_ballot,
    spoil_ballot,
)
from electionguard.elgamal import elgamal_keypair_from_secret
from electionguard.encrypt import encrypt_ballot
from electionguard.group import int_to_q

import electionguardtest.ballot_factory as BallotFactory
import electionguardtest.election_factory as ElectionFactory

election_factory = ElectionFactory.ElectionFactory()
ballot_factory = BallotFactory.BallotFactory()


class TestBallotBox(unittest.TestCase):
    def test_ballot_box_cast_ballot(self):
        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        election = election_factory.get_fake_election()
        metadata, encryption_context = election_factory.get_fake_ciphertext_election(
            election, keypair.public_key
        )
        store = BallotStore()
        source = election_factory.get_fake_ballot(metadata)
        self.assertTrue(source.is_valid(metadata.ballot_styles[0].object_id))

        # Act
        data = encrypt_ballot(source, metadata, encryption_context)
        subject = BallotBox(metadata, encryption_context, store)
        result = subject.cast(data)

        # Assert
        expected = store.get(source.object_id)
        self.assertEqual(expected.state, BallotBoxState.CAST)
        self.assertEqual(result.state, BallotBoxState.CAST)
        self.assertEqual(expected.object_id, result.object_id)

        # Test failure modes
        self.assertIsNone(subject.cast(data))  # cannot cast again
        self.assertIsNone(subject.spoil(data))  # cannot spoil a ballot already cast

    def test_ballot_box_spoil_ballot(self):
        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        election = election_factory.get_fake_election()
        metadata, encryption_context = election_factory.get_fake_ciphertext_election(
            election, keypair.public_key
        )
        store = BallotStore()
        source = election_factory.get_fake_ballot(metadata)
        self.assertTrue(source.is_valid(metadata.ballot_styles[0].object_id))

        # Act
        data = encrypt_ballot(source, metadata, encryption_context)
        subject = BallotBox(metadata, encryption_context, store)
        result = subject.spoil(data)

        # Assert
        expected = store.get(source.object_id)
        self.assertEqual(expected.state, BallotBoxState.SPOILED)
        self.assertEqual(result.state, BallotBoxState.SPOILED)
        self.assertEqual(expected.object_id, result.object_id)

        # Test failure modes
        self.assertIsNone(subject.spoil(data))  # cannot spoil again
        self.assertIsNone(subject.cast(data))  # cannot cast a ballot alraedy spoiled

    def test_cast_ballot(self):
        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        election = election_factory.get_fake_election()
        metadata, encryption_context = election_factory.get_fake_ciphertext_election(
            election, keypair.public_key
        )
        store = BallotStore()
        source = election_factory.get_fake_ballot(metadata)
        self.assertTrue(source.is_valid(metadata.ballot_styles[0].object_id))

        # Act
        data = encrypt_ballot(source, metadata, encryption_context)
        result = cast_ballot(data, metadata, encryption_context, store)

        # Assert
        expected = store.get(source.object_id)
        self.assertEqual(expected.state, BallotBoxState.CAST)
        self.assertEqual(result.state, BallotBoxState.CAST)
        self.assertEqual(expected.object_id, result.object_id)

        # Test failure modes
        self.assertIsNone(
            cast_ballot(data, metadata, encryption_context, store)
        )  # cannot cast again
        self.assertIsNone(
            spoil_ballot(data, metadata, encryption_context, store)
        )  # cannot cspoil a ballot already cast

    def test_spoil_ballot(self):
        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        election = election_factory.get_fake_election()
        metadata, encryption_context = election_factory.get_fake_ciphertext_election(
            election, keypair.public_key
        )
        store = BallotStore()
        source = election_factory.get_fake_ballot(metadata)
        self.assertTrue(source.is_valid(metadata.ballot_styles[0].object_id))

        # Act
        data = encrypt_ballot(source, metadata, encryption_context)
        result = spoil_ballot(data, metadata, encryption_context, store)

        # Assert
        expected = store.get(source.object_id)
        self.assertEqual(expected.state, BallotBoxState.SPOILED)
        self.assertEqual(result.state, BallotBoxState.SPOILED)
        self.assertEqual(expected.object_id, result.object_id)

        # Test failure modes
        self.assertIsNone(
            spoil_ballot(data, metadata, encryption_context, store)
        )  # cannot spoil again
        self.assertIsNone(
            cast_ballot(data, metadata, encryption_context, store)
        )  # cannot cast a ballot already spoiled
