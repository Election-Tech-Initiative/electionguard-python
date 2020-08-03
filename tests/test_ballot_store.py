from unittest import TestCase

from electionguard.ballot import (
    BallotBoxState,
    CiphertextAcceptedBallot,
    make_ciphertext_accepted_ballot,
)
from electionguard.ballot_store import BallotStore

from electionguard.elgamal import elgamal_keypair_from_secret
from electionguard.encrypt import encrypt_ballot, EncryptionDevice
from electionguard.group import int_to_q

import electionguardtest.ballot_factory as BallotFactory
import electionguardtest.election_factory as ElectionFactory

election_factory = ElectionFactory.ElectionFactory()
ballot_factory = BallotFactory.BallotFactory()
SEED_HASH = EncryptionDevice("Location").get_hash()


class TestBallotStore(TestCase):
    def test_ballot_store(self):

        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        election = election_factory.get_fake_election()
        metadata, context = election_factory.get_fake_ciphertext_election(
            election, keypair.public_key
        )

        # get an encrypted fake ballot to work with
        fake_ballot = election_factory.get_fake_ballot(metadata)
        encrypted_ballot = encrypt_ballot(fake_ballot, metadata, context, SEED_HASH)

        # Set up the ballot store
        subject = BallotStore()
        data_cast = make_ciphertext_accepted_ballot(
            encrypted_ballot.object_id,
            encrypted_ballot.ballot_style,
            encrypted_ballot.description_hash,
            encrypted_ballot.previous_tracking_hash,
            encrypted_ballot.contests,
            encrypted_ballot.tracking_hash,
            encrypted_ballot.timestamp,
        )
        data_cast.state = BallotBoxState.CAST

        data_spoiled = make_ciphertext_accepted_ballot(
            encrypted_ballot.object_id,
            encrypted_ballot.ballot_style,
            encrypted_ballot.description_hash,
            encrypted_ballot.previous_tracking_hash,
            encrypted_ballot.contests,
            encrypted_ballot.tracking_hash,
            encrypted_ballot.timestamp,
        )
        data_spoiled.state = BallotBoxState.SPOILED

        self.assertIsNone(subject.get("cast"))
        self.assertIsNone(subject.get("spoiled"))

        # try to set a ballot with an unknown state
        self.assertFalse(
            subject.set(
                "unknown",
                make_ciphertext_accepted_ballot(
                    encrypted_ballot.object_id,
                    encrypted_ballot.ballot_style,
                    encrypted_ballot.description_hash,
                    encrypted_ballot.previous_tracking_hash,
                    encrypted_ballot.contests,
                    encrypted_ballot.tracking_hash,
                    encrypted_ballot.timestamp,
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
