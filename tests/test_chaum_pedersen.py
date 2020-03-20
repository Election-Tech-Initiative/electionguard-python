import unittest
from datetime import timedelta

from hypothesis import given, settings

from electionguard.chaum_pedersen import make_chaum_pedersen_zero, valid_chaum_pedersen, make_chaum_pedersen_one, \
    ChaumPedersenProof
from electionguard.elgamal import ElGamalKeyPair, elgamal_encrypt, elgamal_keypair_from_secret
from electionguard.group import ElementModQ, TWO_MOD_Q, ONE_MOD_Q
from tests.test_elgamal import arb_elgamal_keypair
from tests.test_group import arb_element_mod_q, arb_element_mod_q_no_zero


class TestChaumPedersen(unittest.TestCase):
    def test_cp_proofs_simple(self):
        # doesn't get any simpler than this
        keypair = elgamal_keypair_from_secret(TWO_MOD_Q)
        nonce = ONE_MOD_Q
        seed = TWO_MOD_Q
        message0 = elgamal_encrypt(0, nonce, keypair.public_key)
        proof0 = make_chaum_pedersen_zero(message0, nonce, keypair.public_key, seed)
        proof0bad = make_chaum_pedersen_one(message0, nonce, keypair.public_key, seed)
        self.assertTrue(valid_chaum_pedersen(proof0, keypair.public_key))
        self.assertFalse(valid_chaum_pedersen(proof0bad, keypair.public_key))

        message1 = elgamal_encrypt(1, nonce, keypair.public_key)
        proof1 = make_chaum_pedersen_one(message1, nonce, keypair.public_key, seed)
        proof1bad = make_chaum_pedersen_zero(message1, nonce, keypair.public_key, seed)
        self.assertTrue(valid_chaum_pedersen(proof1, keypair.public_key))
        self.assertFalse(valid_chaum_pedersen(proof1bad, keypair.public_key))

    # These tests are notably slow; we need to give them more time to run than the
    # default 200ms, otherwise Hypothesis kills them for running overtime.
    @settings(deadline=timedelta(milliseconds=2000))
    @given(arb_elgamal_keypair(), arb_element_mod_q_no_zero(), arb_element_mod_q())
    def test_cp_proof_zero(self, keypair: ElGamalKeyPair, nonce: ElementModQ, seed: ElementModQ):
        message = elgamal_encrypt(0, nonce, keypair.public_key)
        proof = make_chaum_pedersen_zero(message, nonce, keypair.public_key, seed)
        proof_bad = make_chaum_pedersen_one(message, nonce, keypair.public_key, seed)
        self.assertTrue(valid_chaum_pedersen(proof, keypair.public_key))
        self.assertFalse(valid_chaum_pedersen(proof_bad, keypair.public_key))

    @settings(deadline=timedelta(milliseconds=2000))
    @given(arb_elgamal_keypair(), arb_element_mod_q_no_zero(), arb_element_mod_q())
    def test_cp_proof_one(self, keypair: ElGamalKeyPair, nonce: ElementModQ, seed: ElementModQ):
        message = elgamal_encrypt(1, nonce, keypair.public_key)
        proof = make_chaum_pedersen_one(message, nonce, keypair.public_key, seed)
        proof_bad = make_chaum_pedersen_zero(message, nonce, keypair.public_key, seed)
        self.assertTrue(valid_chaum_pedersen(proof, keypair.public_key))
        self.assertFalse(valid_chaum_pedersen(proof_bad, keypair.public_key))

    @settings(deadline=timedelta(milliseconds=2000))
    @given(arb_elgamal_keypair(), arb_element_mod_q_no_zero(), arb_element_mod_q())
    def test_cp_proof_broken(self, keypair: ElGamalKeyPair, nonce: ElementModQ, seed: ElementModQ):
        # We're trying to verify two different ways we might generate an invalid C-P proof.
        message0 = elgamal_encrypt(0, nonce, keypair.public_key)
        message2 = elgamal_encrypt(2, nonce, keypair.public_key)
        proof0 = make_chaum_pedersen_zero(message0, nonce, keypair.public_key, seed)
        proof2 = make_chaum_pedersen_zero(message2, nonce, keypair.public_key, seed)
        proof_subst = ChaumPedersenProof(proof2.message, proof0.a0, proof0.b0, proof0.a1, proof0.b1, proof0.c0,
                                         proof0.c1, proof0.v0, proof0.v1)
        self.assertFalse(valid_chaum_pedersen(proof2, keypair.public_key))
        self.assertFalse(valid_chaum_pedersen(proof_subst, keypair.public_key))
