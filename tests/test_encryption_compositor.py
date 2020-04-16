import unittest

from electionguard.encryption_compositor import (
    contest_from,
    encrypt_contest,
    encrypt_selection,
    selection_from
)

from electionguard.ballot import (
    BallotContest,
    BallotSelection
)

from electionguard.election import (
    ContestDescription,
    SelectionDescription,
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

from secrets import randbelow

class TestEncryptionCompositor(unittest.TestCase):

    def test_encrypt_selection_succeeds(self):
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        nonce = randbelow(Q)
        metadata = SelectionDescription("some-selection-object-id", "some-candidate-id", 1)
        hash_context = metadata.crypto_hash()

        subject = selection_from(metadata)

        result = encrypt_selection(subject, metadata, keypair.public_key, nonce)

        self.assertIsNotNone(result)

        self.assertTrue(result.is_valid(hash_context, keypair.public_key))

    # def test_decrypt_selection_succeeds(self):
    #     pass

    def test_encrypt_referendum_contest_suceeds(self):
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        nonce = randbelow(Q)
        metadata = ContestDescription("some-contest-object-id", "some-electoral-district-id", 0, VoteVariationType.one_of_m, 1)
        metadata.ballot_selections = [
            SelectionDescription("some-object-id-affirmative", "some-candidate-id-affirmative", 0),
            SelectionDescription("some-object-id-negative", "some-candidate-id-negative", 1),
        ]
        metadata.votes_allowed = 1
        hash_context = metadata.crypto_hash()

        subject = contest_from(metadata)

        result = encrypt_contest(subject, metadata, keypair.public_key, nonce)

        self.assertIsNotNone(result)

        self.assertTrue(result.is_valid(hash_context, keypair.public_key))