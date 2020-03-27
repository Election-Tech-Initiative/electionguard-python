import unittest
from datetime import timedelta
from random import Random
from typing import Tuple

from hypothesis import HealthCheck
from hypothesis import given, settings
from hypothesis.strategies import integers, composite, emails, booleans, lists

from electionguard.contest import ContestDescription, PlaintextVotedContest, Candidate, encrypt_voted_contest, \
    is_valid_plaintext_voted_contest, is_valid_encrypted_voted_contest, decrypt_voted_contest, \
    EncryptedVotedContest, make_contest_hash
from electionguard.elgamal import ElGamalKeyPair, elgamal_keypair_from_secret
from electionguard.group import ElementModQ, ONE_MOD_Q, int_to_q, add_q
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
    return contest_description, PlaintextVotedContest(make_contest_hash(contest_description), selections)


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
    return contest_description, PlaintextVotedContest(make_contest_hash(contest_description), selections)


class TestContest(unittest.TestCase):
    def test_simple_encryption_decryption_inverses(self):
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        contest = ContestDescription("A", [Candidate("A", False, False, False), Candidate("B", False, False, False)],
                                     "A", "A", "A", "A", 1, 2)
        contest_hash = make_contest_hash(contest)
        nonce = ONE_MOD_Q
        plaintext = PlaintextVotedContest(contest_hash, [1, 0])
        self.assertTrue(is_valid_plaintext_voted_contest(plaintext, contest))
        ciphertext = encrypt_voted_contest(plaintext, contest, keypair.public_key, nonce)
        self.assertTrue(is_valid_encrypted_voted_contest(ciphertext, contest, keypair.public_key))

        plaintext_again = decrypt_voted_contest(ciphertext, contest, keypair)
        self.assertTrue(is_valid_plaintext_voted_contest(plaintext_again, contest))
        self.assertEqual(plaintext, plaintext_again)

    def test_error_conditions(self):
        # to get us to 100% test coverage
        contest = ContestDescription("A", [Candidate("A", False, False, False), Candidate("B", False, False, False),
                                           Candidate("C", False, False, False)],
                                     "A", "A", "A", "A", 2, 3)
        contest_hash = make_contest_hash(contest)
        plaintext = PlaintextVotedContest(contest_hash, [2, 0, 0])
        self.assertFalse(is_valid_plaintext_voted_contest(plaintext, contest))

        plaintext = PlaintextVotedContest(contest_hash, [1, 0, 0])
        self.assertFalse(is_valid_plaintext_voted_contest(plaintext, contest))

        plaintext = PlaintextVotedContest(contest_hash, [1, 1, 1])
        self.assertFalse(is_valid_plaintext_voted_contest(plaintext, contest))

        plaintext = PlaintextVotedContest(add_q(contest_hash, ONE_MOD_Q), [1, 1, 1])
        self.assertFalse(is_valid_plaintext_voted_contest(plaintext, contest))

        keypair = elgamal_keypair_from_secret(int_to_q(2))
        nonce = ONE_MOD_Q
        self.assertRaises(Exception, encrypt_voted_contest, plaintext, keypair.public_key, nonce)

        # now, we're going to mess with the ciphertext
        plaintext = PlaintextVotedContest(contest_hash, [1, 1, 0])
        c = encrypt_voted_contest(plaintext, contest, keypair.public_key, nonce)
        c2 = EncryptedVotedContest(c.contest_hash, c.encrypted_selections[1:], c.zero_or_one_selection_proofs,
                                   c.sum_of_counters_proof)
        self.assertFalse(is_valid_encrypted_voted_contest(c2, contest, keypair.public_key))
        c2 = EncryptedVotedContest(c.contest_hash, c.encrypted_selections, c.zero_or_one_selection_proofs[1:],
                                   c.sum_of_counters_proof)
        self.assertFalse(is_valid_encrypted_voted_contest(c2, contest, keypair.public_key))

    @settings(deadline=timedelta(milliseconds=2000), suppress_health_check=[HealthCheck.too_slow])
    @given(arb_plaintext_voted_contest_well_formed(), arb_elgamal_keypair(), arb_element_mod_q_no_zero())
    def test_encryption_decryption_inverses(self, cp: Tuple[ContestDescription, PlaintextVotedContest],
                                            keypair: ElGamalKeyPair,
                                            nonce: ElementModQ):
        contest_description, plaintext = cp
        self.assertTrue(is_valid_plaintext_voted_contest(plaintext, contest_description))

        ciphertext = encrypt_voted_contest(plaintext, contest_description, keypair.public_key, nonce)
        plaintext_again = decrypt_voted_contest(ciphertext, contest_description, keypair)

        self.assertTrue(is_valid_plaintext_voted_contest(plaintext_again, contest_description))
        self.assertEqual(plaintext, plaintext_again)

    @settings(deadline=timedelta(milliseconds=2000), suppress_health_check=[HealthCheck.too_slow])
    @given(arb_plaintext_voted_contest_overvote(), arb_elgamal_keypair(), arb_element_mod_q_no_zero())
    def test_overvotes_dont_validate(self, cp: Tuple[ContestDescription, PlaintextVotedContest],
                                     keypair: ElGamalKeyPair,
                                     nonce: ElementModQ):
        contest_description, plaintext = cp
        ciphertext = encrypt_voted_contest(plaintext, contest_description, keypair.public_key, nonce,
                                           suppress_validity_check=True)
        self.assertFalse(is_valid_encrypted_voted_contest(ciphertext, contest_description, keypair.public_key))
