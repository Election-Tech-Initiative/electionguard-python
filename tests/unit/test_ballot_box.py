from tests.base_test_case import BaseTestCase

from electionguard.ballot import BallotBoxState
from electionguard.data_store import DataStore

from electionguard.ballot_box import (
    BallotBox,
    accept_ballot,
)
from electionguard.ballot_validator import ballot_is_valid_for_election
from electionguard.constants import get_small_prime
from electionguard.elgamal import elgamal_keypair_from_secret
from electionguard.encrypt import encrypt_ballot
from electionguard.group import int_to_q

import electionguard_tools.factories.ballot_factory as BallotFactory
import electionguard_tools.factories.election_factory as ElectionFactory

election_factory = ElectionFactory.ElectionFactory()
ballot_factory = BallotFactory.BallotFactory()

SEED = election_factory.get_encryption_device().get_hash()


class TestBallotBox(BaseTestCase):
    """Ballot box tests"""

    def test_ballot_box_cast_ballot(self):
        print(get_small_prime())
        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        manifest = election_factory.get_fake_manifest()
        internal_manifest, context = election_factory.get_fake_ciphertext_election(
            manifest, keypair.public_key
        )
        store = DataStore()
        source = election_factory.get_fake_ballot(internal_manifest)
        self.assertTrue(source.is_valid(internal_manifest.ballot_styles[0].object_id))

        # Act
        data = encrypt_ballot(source, internal_manifest, context, SEED)
        self.assertTrue(ballot_is_valid_for_election(data, internal_manifest, context))
        subject = BallotBox(internal_manifest, context, store)
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
        manifest = election_factory.get_fake_manifest()
        internal_manifest, context = election_factory.get_fake_ciphertext_election(
            manifest, keypair.public_key
        )
        store = DataStore()
        source = election_factory.get_fake_ballot(internal_manifest)
        self.assertTrue(source.is_valid(internal_manifest.ballot_styles[0].object_id))

        # Act
        data = encrypt_ballot(source, internal_manifest, context, SEED)
        subject = BallotBox(internal_manifest, context, store)
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
        manifest = election_factory.get_fake_manifest()
        internal_manifest, context = election_factory.get_fake_ciphertext_election(
            manifest, keypair.public_key
        )
        store = DataStore()
        source = election_factory.get_fake_ballot(internal_manifest)
        self.assertTrue(source.is_valid(internal_manifest.ballot_styles[0].object_id))

        # Act
        data = encrypt_ballot(source, internal_manifest, context, SEED)
        result = accept_ballot(
            data, BallotBoxState.CAST, internal_manifest, context, store
        )

        # Assert
        expected = store.get(source.object_id)
        self.assertEqual(expected.state, BallotBoxState.CAST)
        self.assertEqual(result.state, BallotBoxState.CAST)
        self.assertEqual(expected.object_id, result.object_id)

        # Test failure modes
        self.assertIsNone(
            accept_ballot(data, BallotBoxState.CAST, internal_manifest, context, store)
        )  # cannot cast again
        self.assertIsNone(
            accept_ballot(
                data, BallotBoxState.SPOILED, internal_manifest, context, store
            )
        )  # cannot cspoil a ballot already cast

    def test_spoil_ballot(self):
        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        manifest = election_factory.get_fake_manifest()
        internal_manifest, context = election_factory.get_fake_ciphertext_election(
            manifest, keypair.public_key
        )
        store = DataStore()
        source = election_factory.get_fake_ballot(internal_manifest)
        self.assertTrue(source.is_valid(internal_manifest.ballot_styles[0].object_id))

        # Act
        data = encrypt_ballot(source, internal_manifest, context, SEED)
        result = accept_ballot(
            data, BallotBoxState.SPOILED, internal_manifest, context, store
        )

        # Assert
        expected = store.get(source.object_id)
        self.assertEqual(expected.state, BallotBoxState.SPOILED)
        self.assertEqual(result.state, BallotBoxState.SPOILED)
        self.assertEqual(expected.object_id, result.object_id)

        # Test failure modes
        self.assertIsNone(
            accept_ballot(
                data, BallotBoxState.SPOILED, internal_manifest, context, store
            )
        )  # cannot spoil again
        self.assertIsNone(
            accept_ballot(data, BallotBoxState.CAST, internal_manifest, context, store)
        )  # cannot cast a ballot already spoiled
