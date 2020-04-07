import unittest
from datetime import timedelta
from random import Random
from typing import Tuple

from hypothesis import HealthCheck
from hypothesis import given, settings
from hypothesis.strategies import integers, composite, emails, booleans, lists

from electionguard.contest import (
    ContestDescription,
    PlaintextVotedContest,
    Candidate,
    encrypt_voted_contest,
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

    ballot_selections = draw(
        lists(arb_candidate(), min_size=votes_allowed, max_size=votes_allowed)
    )
    assert len(ballot_selections) == votes_allowed
    return ContestDescription(
        draw(strs),
        ballot_selections,
        draw(strs),
        draw(strs),
        draw(strs),
        draw(strs),
        number_elected,
        votes_allowed,
    )


@composite
def arb_contest_description_room_for_overvoting(
    draw, strs=emails(), ints=integers(2, 6)
):
    number_elected = draw(ints)
    votes_allowed = draw(ints)

    if number_elected >= votes_allowed:
        number_elected = votes_allowed - 1

    ballot_selections = draw(
        lists(arb_candidate(), min_size=votes_allowed, max_size=votes_allowed)
    )
    assert len(ballot_selections) == votes_allowed
    return ContestDescription(
        draw(strs),
        ballot_selections,
        draw(strs),
        draw(strs),
        draw(strs),
        draw(strs),
        number_elected,
        votes_allowed,
    )


def contest_description_to_plaintext_voted_context(
    random_seed: int, cds: ContestDescription
) -> PlaintextVotedContest:
    """
    This is used by `arb_plaintext_voted_contest_well_formed` and other generators. Given a contest
    description and a random seed, produce a well-formed plaintext voted contest.
    """
    r = Random()
    r.seed(random_seed)

    # We're going to create a list of numbers, with the right number of 1's and 0's, then shuffle it based on the seed.
    # Note that we're not generating vote selections with undervotes, because those shouldn't exist at this stage in
    # ElectionGuard. If the voter chooses to undervote, the "dummy" votes should become one, and thus there's no such
    # thing as an undervoted ballot plaintext.

    selections = [1] * cds.number_elected + [0] * (
        cds.votes_allowed - cds.number_elected
    )

    assert len(selections) == cds.votes_allowed

    r.shuffle(selections)
    return PlaintextVotedContest(cds.crypto_hash(), selections)


@composite
def arb_plaintext_voted_contest_well_formed(
    draw, cds=arb_contest_description(), seed=integers()
):
    s = draw(seed)
    contest_description: ContestDescription = draw(cds)

    return (
        contest_description,
        contest_description_to_plaintext_voted_context(s, contest_description),
    )


@composite
def arb_plaintext_voted_contest_overvote(
    draw,
    cds=arb_contest_description_room_for_overvoting(),
    seed=integers(),
    overvotes=integers(1, 6),
):
    r = Random()
    r.seed(draw(seed))
    contest_description: ContestDescription = draw(cds)
    overvote: int = draw(overvotes)

    assert contest_description.number_elected < contest_description.votes_allowed

    if (
        contest_description.number_elected + overvote
        > contest_description.votes_allowed
    ):
        overvote = (
            contest_description.votes_allowed - contest_description.number_elected
        )

    selections = [1] * (contest_description.number_elected + overvote) + [0] * (
        contest_description.votes_allowed
        - contest_description.number_elected
        - overvote
    )

    assert len(selections) == contest_description.votes_allowed

    r.shuffle(selections)
    return (
        contest_description,
        PlaintextVotedContest(contest_description.crypto_hash(), selections),
    )


class TestContest(unittest.TestCase):
    def test_simple_encryption_decryption_inverses(self):
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        contest = ContestDescription(
            "A",
            [Candidate("A", False, False, False), Candidate("B", False, False, False)],
            "A",
            "A",
            "A",
            "A",
            1,
            2,
        )
        contest_hash = contest.crypto_hash()
        nonce = ONE_MOD_Q
        plaintext = PlaintextVotedContest(contest_hash, [1, 0])
        self.assertTrue(plaintext.is_valid(contest))
        ciphertext = unwrap_optional(
            encrypt_voted_contest(plaintext, contest, keypair.public_key, nonce)
        )
        self.assertTrue(ciphertext.is_valid(contest, keypair.public_key))

        plaintext_again = ciphertext.decrypt(contest, keypair)
        self.assertTrue(plaintext_again.is_valid(contest))
        self.assertEqual(plaintext, plaintext_again)

    def test_error_conditions(self):
        # try to hit all the error conditions to get higher coverage
        contest = ContestDescription(
            "A",
            [
                Candidate("A", False, False, False),
                Candidate("B", False, False, False),
                Candidate("C", False, False, False),
            ],
            "A",
            "A",
            "A",
            "A",
            2,
            3,
        )
        contest_hash = contest.crypto_hash()
        valid_plaintext = PlaintextVotedContest(contest_hash, [1, 1, 0])
        self.assertTrue(valid_plaintext.is_valid(contest))

        plaintext_bad1 = valid_plaintext._replace(choices=[2, 0, 0])
        self.assertFalse(plaintext_bad1.is_valid(contest))

        plaintext_bad2 = valid_plaintext._replace(choices=[1, 0, 0])
        self.assertFalse(plaintext_bad2.is_valid(contest))

        plaintext_bad3 = valid_plaintext._replace(choices=[1, 1, 1])
        self.assertFalse(plaintext_bad3.is_valid(contest))

        plaintext_bad4 = valid_plaintext._replace(choices=[1, 1, 1, 1])
        self.assertFalse(plaintext_bad4.is_valid(contest))

        plaintext_bad5 = valid_plaintext._replace(
            contest_hash=add_q(contest_hash, ONE_MOD_Q)
        )
        self.assertFalse(plaintext_bad5.is_valid(contest))

        bad_contest = contest._replace(votes_allowed=contest.votes_allowed - 1)
        bad_contest_hash = bad_contest.crypto_hash()
        plaintext_bad6 = valid_plaintext._replace(contest_hash=bad_contest_hash)
        self.assertFalse(plaintext_bad6.is_valid(bad_contest))

        keypair = elgamal_keypair_from_secret(int_to_q(2))
        nonce = ONE_MOD_Q
        self.assertRaises(
            Exception, encrypt_voted_contest, valid_plaintext, keypair.public_key, nonce
        )

        self.assertIsNone(
            encrypt_voted_contest(plaintext_bad1, contest, keypair.public_key, nonce)
        )

        # now, we're going to mess with the ciphertext
        c = unwrap_optional(
            encrypt_voted_contest(valid_plaintext, contest, keypair.public_key, nonce)
        )
        c2 = c._replace(encrypted_selections=c.encrypted_selections[1:])
        self.assertFalse(c2.is_valid(contest, keypair.public_key))
        self.assertIsNone(c2.decrypt(contest, keypair))

        c3 = c._replace(zero_or_one_selection_proofs=c.zero_or_one_selection_proofs[1:])
        self.assertFalse(c3.is_valid(contest, keypair.public_key))

        c4 = c._replace(contest_hash=add_q(c.contest_hash, ONE_MOD_Q))
        self.assertFalse(c4.is_valid(contest, keypair.public_key))

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(
        arb_plaintext_voted_contest_well_formed(),
        arb_elgamal_keypair(),
        arb_element_mod_q_no_zero(),
    )
    def test_encryption_decryption_inverses(
        self,
        cp: Tuple[ContestDescription, PlaintextVotedContest],
        keypair: ElGamalKeyPair,
        nonce: ElementModQ,
    ):
        contest_description, plaintext = cp
        self.assertTrue(plaintext.is_valid(contest_description))

        ciphertext = unwrap_optional(
            encrypt_voted_contest(
                plaintext, contest_description, keypair.public_key, nonce
            )
        )
        plaintext_again = unwrap_optional(
            ciphertext.decrypt(contest_description, keypair)
        )

        self.assertTrue(plaintext_again.is_valid(contest_description))
        self.assertEqual(plaintext, plaintext_again)

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(
        arb_plaintext_voted_contest_overvote(),
        arb_elgamal_keypair(),
        arb_element_mod_q_no_zero(),
    )
    def test_overvotes_dont_validate(
        self,
        cp: Tuple[ContestDescription, PlaintextVotedContest],
        keypair: ElGamalKeyPair,
        nonce: ElementModQ,
    ):
        contest_description, plaintext = cp
        ciphertext = unwrap_optional(
            encrypt_voted_contest(
                plaintext,
                contest_description,
                keypair.public_key,
                nonce,
                suppress_validity_check=True,
            )
        )
        self.assertFalse(ciphertext.is_valid(contest_description, keypair.public_key))

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(
        arb_plaintext_voted_contest_well_formed(),
        arb_elgamal_keypair(),
        arb_element_mod_q_no_zero(),
    )
    def test_encrypt_malformed_plaintext_fails(
        self,
        cp: Tuple[ContestDescription, PlaintextVotedContest],
        keypair: ElGamalKeyPair,
        nonce: ElementModQ,
    ):
        contest_description, plaintext = cp

        evc = encrypt_voted_contest(
            plaintext,
            contest_description,
            keypair.public_key,
            nonce,
            suppress_validity_check=True,
        )
        self.assertIsNotNone(evc)

        # malformed plaintext with counters out of range should cause elgamal_encrypt to return None
        bad_plaintext = plaintext._replace(choices=[s + Q for s in plaintext.choices])

        self.assertIsNone(
            encrypt_voted_contest(
                bad_plaintext,
                contest_description,
                keypair.public_key,
                nonce,
                suppress_validity_check=True,
            )
        )

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(
        arb_plaintext_voted_contest_well_formed(),
        arb_elgamal_keypair(),
        arb_element_mod_q_no_zero(),
    )
    def test_encrypt_malformed_ciphertext_fails(
        self,
        cp: Tuple[ContestDescription, PlaintextVotedContest],
        keypair: ElGamalKeyPair,
        nonce: ElementModQ,
    ):
        contest_description, plaintext = cp

        evc = encrypt_voted_contest(
            plaintext,
            contest_description,
            keypair.public_key,
            nonce,
            suppress_validity_check=True,
        )
        self.assertIsNotNone(evc)
        self.assertTrue(evc.is_valid(contest_description, keypair.public_key))

        # now we tamper with the evc to make sure the verification fails
        bad_selections = evc.encrypted_selections.copy()
        bad_selections[0] = bad_selections[0]._replace(
            alpha=mult_p(bad_selections[0].alpha, TWO_MOD_P)
        )
        bad_evc = evc._replace(encrypted_selections=bad_selections)
        self.assertFalse(bad_evc.is_valid(contest_description, keypair.public_key))

        # and we'll also tamper with the disjunctive proof
        bad_proofs = evc.zero_or_one_selection_proofs.copy()
        bad_proofs[0] = bad_proofs[0]._replace(a0=mult_p(bad_proofs[0].a0, TWO_MOD_P))
        bad_evc2 = evc._replace(zero_or_one_selection_proofs=bad_proofs)
        self.assertFalse(bad_evc2.is_valid(contest_description, keypair.public_key))

        # and lastly the accumulation proof
        sum_proof = evc.sum_of_counters_proof
        bad_sum_proof = sum_proof._replace(constant=sum_proof.constant + 1)
        bad_evc3 = evc._replace(sum_of_counters_proof=bad_sum_proof)
        self.assertFalse(bad_evc3.is_valid(contest_description, keypair.public_key))

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=30,
    )
    @given(
        arb_plaintext_voted_contest_well_formed(),
        integers(),
        arb_element_mod_q_no_zero(),
        arb_elgamal_keypair(),
    )
    def test_encrypted_voted_contest_hash(
        self,
        cp: Tuple[ContestDescription, PlaintextVotedContest],
        seed: int,
        eg_seed: ElementModQ,
        keypair: ElGamalKeyPair,
    ):
        pvc1 = cp[1]
        pvc2 = contest_description_to_plaintext_voted_context(seed, cp[0])

        evc1 = encrypt_voted_contest(pvc1, cp[0], keypair.public_key, eg_seed)
        evc2 = encrypt_voted_contest(pvc2, cp[0], keypair.public_key, eg_seed)

        h1 = evc1.crypto_hash()
        h2 = evc2.crypto_hash()
        if pvc1 == pvc2:
            self.assertEqual(h1, h2)

        if h1 != h2:
            self.assertNotEqual(pvc1, pvc2)
