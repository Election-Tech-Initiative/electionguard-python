import unittest
from datetime import timedelta

from hypothesis import given, settings, assume
from hypothesis.strategies import integers

from electionguard.chaum_pedersen import make_disjunctive_chaum_pedersen_zero, is_valid_disjunctive_chaum_pedersen, \
    make_disjunctive_chaum_pedersen_one, DisjunctiveChaumPedersenProof, make_constant_chaum_pedersen, \
    is_valid_constant_chaum_pedersen, make_disjunctive_chaum_pedersen
from electionguard.elgamal import ElGamalKeyPair, elgamal_encrypt, elgamal_keypair_from_secret
from electionguard.group import ElementModQ, TWO_MOD_Q, ONE_MOD_Q
from tests.test_elgamal import arb_elgamal_keypair
from tests.test_group import arb_element_mod_q, arb_element_mod_q_no_zero


class TestDisjunctiveChaumPedersen(unittest.TestCase):
    def test_djcp_proofs_simple(self):
        # doesn't get any simpler than this
        keypair = elgamal_keypair_from_secret(TWO_MOD_Q)
        nonce = ONE_MOD_Q
        seed = TWO_MOD_Q
        message0 = elgamal_encrypt(0, nonce, keypair.public_key)
        proof0 = make_disjunctive_chaum_pedersen_zero(message0, nonce, keypair.public_key, seed)
        proof0bad = make_disjunctive_chaum_pedersen_one(message0, nonce, keypair.public_key, seed)
        self.assertTrue(is_valid_disjunctive_chaum_pedersen(proof0, keypair.public_key))
        self.assertFalse(is_valid_disjunctive_chaum_pedersen(proof0bad, keypair.public_key))

        message1 = elgamal_encrypt(1, nonce, keypair.public_key)
        proof1 = make_disjunctive_chaum_pedersen_one(message1, nonce, keypair.public_key, seed)
        proof1bad = make_disjunctive_chaum_pedersen_zero(message1, nonce, keypair.public_key, seed)
        self.assertTrue(is_valid_disjunctive_chaum_pedersen(proof1, keypair.public_key))
        self.assertFalse(is_valid_disjunctive_chaum_pedersen(proof1bad, keypair.public_key))

    def test_djcp_proof_invalid_inputs(self):
        # this is here to push up our coverage
        keypair = elgamal_keypair_from_secret(TWO_MOD_Q)
        nonce = ONE_MOD_Q
        seed = TWO_MOD_Q
        message0 = elgamal_encrypt(0, nonce, keypair.public_key)
        self.assertRaises(Exception, make_disjunctive_chaum_pedersen, message0, nonce, keypair.public_key, seed, 3)

    # These tests are notably slow; we need to give them more time to run than the
    # default 200ms, otherwise Hypothesis kills them for running overtime.
    @settings(deadline=timedelta(milliseconds=2000))
    @given(arb_elgamal_keypair(), arb_element_mod_q_no_zero(), arb_element_mod_q())
    def test_djcp_proof_zero(self, keypair: ElGamalKeyPair, nonce: ElementModQ, seed: ElementModQ):
        message = elgamal_encrypt(0, nonce, keypair.public_key)
        proof = make_disjunctive_chaum_pedersen_zero(message, nonce, keypair.public_key, seed)
        proof_bad = make_disjunctive_chaum_pedersen_one(message, nonce, keypair.public_key, seed)
        self.assertTrue(is_valid_disjunctive_chaum_pedersen(proof, keypair.public_key))
        self.assertFalse(is_valid_disjunctive_chaum_pedersen(proof_bad, keypair.public_key))

    @settings(deadline=timedelta(milliseconds=2000))
    @given(arb_elgamal_keypair(), arb_element_mod_q_no_zero(), arb_element_mod_q())
    def test_djcp_proof_one(self, keypair: ElGamalKeyPair, nonce: ElementModQ, seed: ElementModQ):
        message = elgamal_encrypt(1, nonce, keypair.public_key)
        proof = make_disjunctive_chaum_pedersen_one(message, nonce, keypair.public_key, seed)
        proof_bad = make_disjunctive_chaum_pedersen_zero(message, nonce, keypair.public_key, seed)
        self.assertTrue(is_valid_disjunctive_chaum_pedersen(proof, keypair.public_key))
        self.assertFalse(is_valid_disjunctive_chaum_pedersen(proof_bad, keypair.public_key))

    @settings(deadline=timedelta(milliseconds=2000))
    @given(arb_elgamal_keypair(), arb_element_mod_q_no_zero(), arb_element_mod_q())
    def test_djcp_proof_broken(self, keypair: ElGamalKeyPair, nonce: ElementModQ, seed: ElementModQ):
        # We're trying to verify two different ways we might generate an invalid C-P proof.
        message0 = elgamal_encrypt(0, nonce, keypair.public_key)
        message2 = elgamal_encrypt(2, nonce, keypair.public_key)
        proof0 = make_disjunctive_chaum_pedersen_zero(message0, nonce, keypair.public_key, seed)
        proof2 = make_disjunctive_chaum_pedersen_zero(message2, nonce, keypair.public_key, seed)
        proof_subst = DisjunctiveChaumPedersenProof(proof2.message, proof0.a0, proof0.b0, proof0.a1, proof0.b1, proof0.c0,
                                                    proof0.c1, proof0.v0, proof0.v1)
        self.assertFalse(is_valid_disjunctive_chaum_pedersen(proof2, keypair.public_key))
        self.assertFalse(is_valid_disjunctive_chaum_pedersen(proof_subst, keypair.public_key))


class TestConstantChaumPedersen(unittest.TestCase):
    def test_ccp_proofs_simple_0(self):
        keypair = elgamal_keypair_from_secret(TWO_MOD_Q)
        nonce = ONE_MOD_Q
        seed = TWO_MOD_Q
        message = elgamal_encrypt(0, nonce, keypair.public_key)
        proof = make_constant_chaum_pedersen(message, 0, nonce, keypair.public_key, seed)
        bad_proof = make_constant_chaum_pedersen(message, 1, nonce, keypair.public_key, seed)
        self.assertTrue(is_valid_constant_chaum_pedersen(proof, keypair.public_key))
        self.assertFalse(is_valid_constant_chaum_pedersen(bad_proof, keypair.public_key))

    def test_ccp_proofs_simple_1(self):
        keypair = elgamal_keypair_from_secret(TWO_MOD_Q)
        nonce = ONE_MOD_Q
        seed = TWO_MOD_Q
        message = elgamal_encrypt(1, nonce, keypair.public_key)
        proof = make_constant_chaum_pedersen(message, 1, nonce, keypair.public_key, seed)
        bad_proof = make_constant_chaum_pedersen(message, 0, nonce, keypair.public_key, seed)
        self.assertTrue(is_valid_constant_chaum_pedersen(proof, keypair.public_key))
        self.assertFalse(is_valid_constant_chaum_pedersen(bad_proof, keypair.public_key))

    @settings(deadline=timedelta(milliseconds=2000))
    @given(arb_elgamal_keypair(), arb_element_mod_q_no_zero(), arb_element_mod_q(), integers(0, 100), integers(0, 100))
    def test_ccp_proof(self, keypair: ElGamalKeyPair, nonce: ElementModQ, seed: ElementModQ, constant: int, bad_constant: int):
        assume(constant != bad_constant)
        message = elgamal_encrypt(constant, nonce, keypair.public_key)
        message_bad = elgamal_encrypt(bad_constant, nonce, keypair.public_key)
        proof = make_constant_chaum_pedersen(message, constant, nonce, keypair.public_key, seed)
        bad_proof = make_constant_chaum_pedersen(message_bad, constant, nonce, keypair.public_key, seed)
        bad_proof2 = make_constant_chaum_pedersen(message, bad_constant, nonce, keypair.public_key, seed)
        self.assertTrue(is_valid_constant_chaum_pedersen(proof, keypair.public_key))
        self.assertFalse(is_valid_constant_chaum_pedersen(bad_proof, keypair.public_key))
        self.assertFalse(is_valid_constant_chaum_pedersen(bad_proof2, keypair.public_key))

