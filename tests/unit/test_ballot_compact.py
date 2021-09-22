from tests.base_test_case import BaseTestCase

from electionguard.ballot import (
    BallotBoxState,
    PlaintextBallot,
    SubmittedBallot,
    from_ciphertext_ballot,
)
from electionguard.ballot_compact import (
    compress_plaintext_ballot,
    compress_submitted_ballot,
    expand_compact_plaintext_ballot,
    expand_compact_submitted_ballot,
)
from electionguard.election import CiphertextElectionContext
from electionguard.elgamal import elgamal_keypair_from_secret
from electionguard.encrypt import encrypt_ballot
from electionguard.group import ElementModQ, int_to_q
from electionguard.manifest import InternalManifest

from electionguard_tools.factories.election_factory import ElectionFactory


class TestCompactBallot(BaseTestCase):
    """Test Compact Ballot Variations"""

    plaintext_ballot: PlaintextBallot
    ballot_nonce: ElementModQ
    submitted_ballot: SubmittedBallot
    internal_manifest: InternalManifest
    context: CiphertextElectionContext

    def setUp(self) -> None:
        # Election setup
        election_factory = ElectionFactory()
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        manifest = election_factory.get_fake_manifest()
        (
            self.internal_manifest,
            self.context,
        ) = election_factory.get_fake_ciphertext_election(manifest, keypair.public_key)
        device_hash = ElectionFactory.get_encryption_device().get_hash()

        # Arrange ballots
        self.plaintext_ballot = election_factory.get_fake_ballot(self.internal_manifest)
        ciphertext_ballot = encrypt_ballot(
            self.plaintext_ballot, self.internal_manifest, self.context, device_hash
        )
        self.ballot_nonce = ciphertext_ballot.nonce
        self.submitted_ballot = from_ciphertext_ballot(
            ciphertext_ballot, BallotBoxState.CAST
        )

    def test_compact_plaintext_ballot(self) -> None:
        # Act
        compact_ballot = compress_plaintext_ballot(self.plaintext_ballot)

        # Assert
        self.assertIsNotNone(compact_ballot)
        self.assertEqual(self.plaintext_ballot.object_id, compact_ballot.object_id)

        # Act
        expanded_ballot = expand_compact_plaintext_ballot(
            compact_ballot, self.internal_manifest
        )

        # Assert
        self.assertIsNotNone(expanded_ballot)
        self.assertEqual(self.plaintext_ballot, expanded_ballot)

    def test_compact_submitted_ballot(self) -> None:
        # Act
        compact_ballot = compress_submitted_ballot(
            self.submitted_ballot, self.plaintext_ballot, self.ballot_nonce
        )

        # Assert
        self.assertIsNotNone(compact_ballot)
        self.assertEqual(
            self.submitted_ballot.object_id,
            compact_ballot.compact_plaintext_ballot.object_id,
        )

        # Act
        expanded_ballot = expand_compact_submitted_ballot(
            compact_ballot, self.internal_manifest, self.context
        )

        # Assert
        self.assertIsNotNone(expanded_ballot)
        self.assertEqual(self.submitted_ballot, expanded_ballot)
        self.assertEqual(self.submitted_ballot.crypto_hash, expanded_ballot.crypto_hash)
