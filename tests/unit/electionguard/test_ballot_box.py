from tests.base_test_case import BaseTestCase

from electionguard.ballot import BallotBoxState
from electionguard.ballot_box import (
    BallotBox,
    submit_ballot_to_box,
    cast_ballot,
    spoil_ballot,
    submit_ballot,
)
from electionguard.data_store import DataStore
from electionguard.elgamal import elgamal_keypair_from_secret
from electionguard.encrypt import encrypt_ballot
from electionguard.group import TWO_MOD_Q
from electionguard.utils import get_optional

import electionguard_tools.factories.election_factory as ElectionFactory


class TestBallotBox(BaseTestCase):
    """Ballot box tests"""

    def setUp(self) -> None:
        """Setup ballot box tests by creating a mock ballot, manifest, and encryption context."""

        election_factory = ElectionFactory.ElectionFactory()
        self.seed = election_factory.get_encryption_device().get_hash()
        keypair = get_optional(elgamal_keypair_from_secret(TWO_MOD_Q))
        manifest = election_factory.get_fake_manifest()
        (
            self.internal_manifest,
            self.context,
        ) = election_factory.get_fake_ciphertext_election(manifest, keypair.public_key)
        self.ballot = election_factory.get_fake_ballot(manifest)

    def test_ballot_box_cast_ballot(self) -> None:
        # Arrange
        encrypted_ballot = get_optional(
            encrypt_ballot(
                self.ballot,
                self.internal_manifest,
                self.context,
                self.seed,
            )
        )
        store: DataStore = DataStore()

        # Act
        ballot_box = BallotBox(self.internal_manifest, self.context, store)
        submitted_ballot = ballot_box.cast(encrypted_ballot)

        # Assert
        # Test returned ballot
        self.assertIsNotNone(submitted_ballot)
        self.assertEqual(submitted_ballot.state, BallotBoxState.CAST)

        # Test ballot in box
        ballot_in_box = store.get(encrypted_ballot.object_id)
        self.assertIsNotNone(ballot_in_box)
        self.assertEqual(ballot_in_box.state, BallotBoxState.CAST)
        self.assertEqual(ballot_in_box.object_id, submitted_ballot.object_id)

        # Test failure modes
        self.assertIsNone(ballot_box.cast(encrypted_ballot))  # cannot cast again
        self.assertIsNone(
            ballot_box.spoil(encrypted_ballot)
        )  # cannot spoil a ballot already cast

    def test_ballot_box_spoil_ballot(self) -> None:
        # Arrange
        encrypted_ballot = get_optional(
            encrypt_ballot(
                self.ballot,
                self.internal_manifest,
                self.context,
                self.seed,
            )
        )
        store: DataStore = DataStore()

        # Act
        ballot_box = BallotBox(self.internal_manifest, self.context, store)
        submitted_ballot = ballot_box.spoil(encrypted_ballot)

        # Assert
        # Test returned ballot
        self.assertIsNotNone(submitted_ballot)
        self.assertEqual(submitted_ballot.state, BallotBoxState.SPOILED)

        # Test ballot in box
        ballot_in_box = store.get(encrypted_ballot.object_id)
        self.assertIsNotNone(ballot_in_box)
        self.assertEqual(ballot_in_box.state, BallotBoxState.SPOILED)
        self.assertEqual(ballot_in_box.object_id, submitted_ballot.object_id)

        # Test failure modes
        self.assertIsNone(ballot_box.cast(encrypted_ballot))  # cannot cast again
        self.assertIsNone(
            ballot_box.spoil(encrypted_ballot)
        )  # cannot spoil a ballot already cast

    def test_submit_ballot_to_box(self) -> None:
        # Arrange
        encrypted_ballot = get_optional(
            encrypt_ballot(
                self.ballot,
                self.internal_manifest,
                self.context,
                self.seed,
            )
        )
        store: DataStore = DataStore()

        # Act
        submitted_ballot = submit_ballot_to_box(
            encrypted_ballot,
            BallotBoxState.CAST,
            self.internal_manifest,
            self.context,
            store,
        )

        # Assert
        # Test returned ballot
        self.assertIsNotNone(submitted_ballot)
        self.assertEqual(submitted_ballot.state, BallotBoxState.CAST)

        # Test ballot in box
        ballot_in_box = store.get(encrypted_ballot.object_id)
        self.assertIsNotNone(ballot_in_box)
        self.assertEqual(ballot_in_box.state, BallotBoxState.CAST)
        self.assertEqual(ballot_in_box.object_id, submitted_ballot.object_id)

        # Test failure modes
        self.assertIsNone(
            submit_ballot_to_box(
                encrypted_ballot,
                BallotBoxState.CAST,
                self.internal_manifest,
                self.context,
                store,
            )
        )  # cannot cast again
        self.assertIsNone(
            submit_ballot_to_box(
                encrypted_ballot,
                BallotBoxState.SPOILED,
                self.internal_manifest,
                self.context,
                store,
            )
        )  # cannot spoil a ballot already cast

    def test_cast_ballot(self) -> None:
        # Arrange
        encrypted_ballot = get_optional(
            encrypt_ballot(
                self.ballot,
                self.internal_manifest,
                self.context,
                self.seed,
            )
        )

        # Act
        submitted_ballot = cast_ballot(encrypted_ballot)

        # Assert
        self.assertIsNotNone(submitted_ballot)
        self.assertEqual(submitted_ballot.state, BallotBoxState.CAST)
        self.assertEqual(encrypted_ballot.object_id, submitted_ballot.object_id)

    def test_spoil_ballot(self) -> None:
        # Arrange
        encrypted_ballot = get_optional(
            encrypt_ballot(
                self.ballot,
                self.internal_manifest,
                self.context,
                self.seed,
            )
        )

        # Act
        submitted_ballot = spoil_ballot(encrypted_ballot)

        # Assert
        self.assertIsNotNone(submitted_ballot)
        self.assertEqual(submitted_ballot.state, BallotBoxState.SPOILED)
        self.assertEqual(encrypted_ballot.object_id, submitted_ballot.object_id)

    def test_submit_ballot(self) -> None:
        # Arrange
        encrypted_ballot = get_optional(
            encrypt_ballot(
                self.ballot,
                self.internal_manifest,
                self.context,
                self.seed,
            )
        )

        # Act
        submitted_ballot = submit_ballot(encrypted_ballot, BallotBoxState.CAST)

        # Assert
        self.assertIsNotNone(submitted_ballot)
        self.assertEqual(submitted_ballot.state, BallotBoxState.CAST)
        self.assertEqual(encrypted_ballot.object_id, submitted_ballot.object_id)
