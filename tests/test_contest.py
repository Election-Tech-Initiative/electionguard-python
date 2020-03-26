import unittest
from datetime import timedelta
from random import Random

from hypothesis import given, settings
from hypothesis.strategies import integers, composite, emails, booleans, lists
from hypothesis import HealthCheck

from electionguard.contest import ContestDescription, PlaintextVotedContest, Candidate, \
    encrypt_voted_contest, \
    is_valid_plaintext_voted_contest, is_valid_encrypted_voted_contest, decrypt_voted_contest, EncryptedVotedContest
from electionguard.elgamal import ElGamalKeyPair, elgamal_keypair_from_secret
from electionguard.group import ElementModQ, ONE_MOD_Q, int_to_q
from tests.test_elgamal import arb_elgamal_keypair
from tests.test_group import arb_element_mod_q_no_zero


@composite
def arb_candidate(draw, strs=emails(), bools=booleans()):
    # We could use a more general definition of candidate names, including unicode, but arbitrary "email addresses"
    # are good enough to stress test things without generating unreadable test results.
    return Candidate(draw(strs), draw(bools), draw(bools), draw(bools))


@composite
def arb_contest_description(draw, strs=emails(), ints=integers(1, 6)):
    number_elected = draw(ints)
    votes_allowed = draw(ints)

    # we have to satisfy an invariant that number_elected <= votes_allowed
    if number_elected > votes_allowed:
        number_elected = votes_allowed

    ballot_selections = draw(lists(arb_candidate(), min_size=votes_allowed, max_size=votes_allowed))
    assert len(ballot_selections) == votes_allowed
    return ContestDescription(draw(strs), ballot_selections, draw(strs), draw(strs), draw(strs), draw(strs),
                              number_elected,
                              votes_allowed)


@composite
def arb_contest_description_room_for_overvoting(draw, strs=emails(), ints=integers(2, 6)):
    number_elected = draw(ints)
    votes_allowed = draw(ints)

    if number_elected >= votes_allowed:
        number_elected = votes_allowed - 1

    ballot_selections = draw(lists(arb_candidate(), min_size=votes_allowed, max_size=votes_allowed))
    assert len(ballot_selections) == votes_allowed
    return ContestDescription(draw(strs), ballot_selections, draw(strs), draw(strs), draw(strs), draw(strs),
                              number_elected,
                              votes_allowed)


@composite
def arb_plaintext_voted_contest_well_formed(draw, cds=arb_contest_description(), seed=integers()):
    r = Random()
    r.seed(draw(seed))
    contest_description: ContestDescription = draw(cds)

    # We're going to create a list of numbers, with the right number of 1's and 0's, then shuffle it based on the seed.
    # Note that we're not generating vote selections with undervotes, because those shouldn't exist at this stage in
    # ElectionGuard. If the voter chooses to undervote, the "dummy" votes should become one, and thus there's no such
    # thing as an undervoted ballot plaintext.

    selections = [1] * contest_description.number_elected + \
                 [0] * (contest_description.votes_allowed - contest_description.number_elected)

    assert len(selections) == contest_description.votes_allowed

    r.shuffle(selections)
    return PlaintextVotedContest(contest_description, selections)


@composite
def arb_plaintext_voted_contest_overvote(draw, cds=arb_contest_description_room_for_overvoting(), seed=integers(),
                                         overvotes=integers(1, 6)):
    r = Random()
    r.seed(draw(seed))
    contest_description: ContestDescription = draw(cds)
    overvote: int = draw(overvotes)

    assert contest_description.number_elected < contest_description.votes_allowed

    if contest_description.number_elected + overvote > contest_description.votes_allowed:
        overvote = contest_description.votes_allowed - contest_description.number_elected

    selections = [1] * (contest_description.number_elected + overvote) + \
                 [0] * (contest_description.votes_allowed - contest_description.number_elected - overvote)

    assert len(selections) == contest_description.votes_allowed

    r.shuffle(selections)
    return PlaintextVotedContest(contest_description, selections)


class TestContest(unittest.TestCase):
    def test_simple_encryption_decryption_inverses(self):
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        contest = ContestDescription("A", [Candidate("A", False, False, False), Candidate("B", False, False, False)],
                                     "A", "A", "A", "A", 1, 2)
        nonce = ONE_MOD_Q
        plaintext = PlaintextVotedContest(contest, [1, 0])
        self.assertTrue(is_valid_plaintext_voted_contest(plaintext))
        ciphertext = encrypt_voted_contest(plaintext, keypair.public_key, nonce)
        self.assertTrue(is_valid_encrypted_voted_contest(ciphertext, plaintext.contest, keypair.public_key))

        plaintext_again = decrypt_voted_contest(ciphertext, plaintext.contest, keypair)
        self.assertTrue(is_valid_plaintext_voted_contest(plaintext_again))
        self.assertEqual(plaintext, plaintext_again)

    def test_error_conditions(self):
        # to get us to 100% test coverage
        contest = ContestDescription("A", [Candidate("A", False, False, False), Candidate("B", False, False, False),
                                           Candidate("C", False, False, False)],
                                     "A", "A", "A", "A", 2, 3)
        plaintext = PlaintextVotedContest(contest, [2, 0, 0])
        self.assertFalse(is_valid_plaintext_voted_contest(plaintext))

        plaintext = PlaintextVotedContest(contest, [1, 0, 0])
        self.assertFalse(is_valid_plaintext_voted_contest(plaintext))

        plaintext = PlaintextVotedContest(contest, [1, 1, 1])
        self.assertFalse(is_valid_plaintext_voted_contest(plaintext))

        keypair = elgamal_keypair_from_secret(int_to_q(2))
        nonce = ONE_MOD_Q
        self.assertRaises(Exception, encrypt_voted_contest, plaintext, keypair.public_key, nonce)

        # now, we're going to mess with the ciphertext
        plaintext = PlaintextVotedContest(contest, [1, 1, 0])
        c = encrypt_voted_contest(plaintext, keypair.public_key, nonce)
        c2 = EncryptedVotedContest(c.contest_hash, c.encrypted_selections[1:], c.zero_or_one_selection_proofs,
                                   c.sum_of_counters_proof)
        self.assertFalse(is_valid_encrypted_voted_contest(c2, plaintext.contest, keypair.public_key))
        c2 = EncryptedVotedContest(c.contest_hash, c.encrypted_selections, c.zero_or_one_selection_proofs[1:],
                                   c.sum_of_counters_proof)
        self.assertFalse(is_valid_encrypted_voted_contest(c2, plaintext.contest, keypair.public_key))

    @settings(deadline=timedelta(milliseconds=2000), suppress_health_check=[HealthCheck.too_slow])
    @given(arb_plaintext_voted_contest_well_formed(), arb_elgamal_keypair(), arb_element_mod_q_no_zero())
    def test_encryption_decryption_inverses(self, plaintext: PlaintextVotedContest, keypair: ElGamalKeyPair,
                                            nonce: ElementModQ):
        self.assertTrue(is_valid_plaintext_voted_contest(plaintext))

        ciphertext = encrypt_voted_contest(plaintext, keypair.public_key, nonce)
        self.assertTrue(is_valid_encrypted_voted_contest(ciphertext, plaintext.contest, keypair.public_key))

        plaintext_again = decrypt_voted_contest(ciphertext, plaintext.contest, keypair)
        self.assertTrue(is_valid_plaintext_voted_contest(plaintext_again))
        self.assertEqual(plaintext, plaintext_again)

    @settings(deadline=timedelta(milliseconds=2000), suppress_health_check=[HealthCheck.too_slow])
    @given(arb_plaintext_voted_contest_overvote(), arb_elgamal_keypair(), arb_element_mod_q_no_zero())
    def test_overvotes_dont_validate(self, plaintext: PlaintextVotedContest, keypair: ElGamalKeyPair,
                                     nonce: ElementModQ):
        ciphertext = encrypt_voted_contest(plaintext, keypair.public_key, nonce, suppress_validity_check=True)
        self.assertFalse(is_valid_encrypted_voted_contest(ciphertext, plaintext.contest, keypair.public_key))
