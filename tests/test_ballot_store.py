import unittest

from electionguard.ballot import BallotBoxState, CiphertextAcceptedBallot
from electionguard.ballot_store import BallotStore

from electionguard.elgamal import elgamal_keypair_from_secret
from electionguard.encrypt import encrypt_ballot
from electionguard.group import int_to_q

import electionguardtest.ballot_factory as BallotFactory
import electionguardtest.election_factory as ElectionFactory

election_factory = ElectionFactory.ElectionFactory()
ballot_factory = BallotFactory.BallotFactory()


class TestBallotStore(unittest.TestCase):
    def test_ballot_store(self):

        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        election = election_factory.get_fake_election()
        metadata, encryption_context = election_factory.get_fake_ciphertext_election(
            election, keypair.public_key
        )

        # get an encrypted fake ballot to work with
        fake_ballot = election_factory.get_fake_ballot(metadata)
        encrypted_ballot = encrypt_ballot(fake_ballot, metadata, encryption_context)

        # Set up the ballot store
        subject = BallotStore()
        data_cast = CiphertextAcceptedBallot(
            encrypted_ballot.object_id,
            encrypted_ballot.ballot_style,
            encrypted_ballot.description_hash,
            encrypted_ballot.contests,
        )
        data_cast.state = BallotBoxState.CAST

        data_spoiled = CiphertextAcceptedBallot(
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
                CiphertextAcceptedBallot(
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
