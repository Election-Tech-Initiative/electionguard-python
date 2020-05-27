import unittest
import os
from typing import Tuple

from datetime import timedelta

from electionguard.ballot_box import (
    BallotBox,
    BallotBoxCiphertextBallot,
    BallotBoxState,
    BallotStore,
    cast_ballot,
    spoil_ballot,
)
from electionguard.elgamal import (
    ElGamalKeyPair,
    elgamal_keypair_from_secret,
    elgamal_add,
)
from electionguard.encrypt import (
    contest_from,
    encrypt_ballot,
    encrypt_contest,
    encrypt_selection,
    selection_from,
    EncryptionCompositor,
)
from electionguard.group import (
    ElementModQ,
    TWO_MOD_Q,
    int_to_q,
    add_q,
    Q,
    TWO_MOD_P,
    mult_p,
)

import electionguardtest.ballot_factory as BallotFactory
import electionguardtest.election_factory as ElectionFactory

election_factory = ElectionFactory.ElectionFactory()
ballot_factory = BallotFactory.BallotFactory()


class TestBallotBox(unittest.TestCase):
    def test_ballot_box_cast_ballot(self):
        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        election = election_factory.get_fake_election()
        metadata, encryption_context = election_factory.get_fake_cyphertext_election(
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
        metadata, encryption_context = election_factory.get_fake_cyphertext_election(
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

    def test_ballot_store(self):

        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        election = election_factory.get_fake_election()
        metadata, encryption_context = election_factory.get_fake_cyphertext_election(
            election, keypair.public_key
        )

        # get an encrypted fake ballot to work with
        fake_ballot = election_factory.get_fake_ballot(metadata)
        encrypted_ballot = encrypt_ballot(fake_ballot, metadata, encryption_context)

        # Set up the ballot store
        subject = BallotStore()
        data_cast = BallotBoxCiphertextBallot(
            encrypted_ballot.object_id,
            encrypted_ballot.ballot_style,
            encrypted_ballot.description_hash,
            encrypted_ballot.contests,
        )
        data_cast.state = BallotBoxState.CAST

        data_spoiled = BallotBoxCiphertextBallot(
            encrypted_ballot.object_id,
            encrypted_ballot.ballot_style,
            encrypted_ballot.description_hash,
            encrypted_ballot.contests,
        )
        data_spoiled.state = BallotBoxState.SPOILED

        self.assertIsNone(subject.get("cast"))
        self.assertIsNone(subject.get("spoiled"))

        # try to set a ballot with an unknown state
        self.assertFalse(
            subject.set(
                "unknown",
                BallotBoxCiphertextBallot(
                    encrypted_ballot.object_id,
                    encrypted_ballot.ballot_style,
                    encrypted_ballot.description_hash,
                    encrypted_ballot.contests,
                ),
            )
        )

        # Act
        self.assertTrue(subject.set("cast", data_cast))
        self.assertTrue(subject.set("spoiled", data_spoiled))

        self.assertEqual(subject.get("cast"), data_cast)
        self.assertEqual(subject.get("spoiled"), data_spoiled)

        self.assertEqual(subject.exists("cast"), (True, data_cast))
        self.assertEqual(subject.exists("spoiled"), (True, data_spoiled))

        # test mutate state
        data_cast.state = BallotBoxState.UNKNOWN
        self.assertEqual(subject.exists("cast"), (False, data_cast))

        # test remove
        self.assertTrue(subject.set("cast", None))
        self.assertEqual(subject.exists("cast"), (False, None))

    def test_cast_ballot(self):
        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        election = election_factory.get_fake_election()
        metadata, encryption_context = election_factory.get_fake_cyphertext_election(
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
        metadata, encryption_context = election_factory.get_fake_cyphertext_election(
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
