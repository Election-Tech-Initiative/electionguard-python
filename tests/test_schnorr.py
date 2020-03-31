import unittest

from hypothesis import given, assume

from electionguard.elgamal import ElGamalKeyPair, elgamal_keypair_from_secret
from electionguard.group import ElementModQ, ElementModP, ZERO_MOD_P, P, int_to_p_unchecked, TWO_MOD_Q, ONE_MOD_Q
from electionguard.schnorr import make_schnorr_proof, is_valid_schnorr_proof, SchnorrProof
from tests.test_elgamal import arb_elgamal_keypair
from tests.test_group import arb_element_mod_q, arb_element_mod_p_no_zero, arb_element_mod_p


class TestSchnorr(unittest.TestCase):
    def test_schnorr_proofs_simple(self):
        # doesn't get any simpler than this
        keypair = elgamal_keypair_from_secret(TWO_MOD_Q)
        nonce = ONE_MOD_Q
        proof = make_schnorr_proof(keypair, nonce)
        self.assertTrue(is_valid_schnorr_proof(proof))

    @given(arb_elgamal_keypair(), arb_element_mod_q())
    def test_schnorr_proofs_valid(self, keypair: ElGamalKeyPair, nonce: ElementModQ):
        proof = make_schnorr_proof(keypair, nonce)
        self.assertTrue(is_valid_schnorr_proof(proof))

    # Now, we introduce errors in the proofs and make sure that they fail to verify
    @given(arb_elgamal_keypair(), arb_element_mod_q(), arb_element_mod_q())
    def test_schnorr_proofs_invalid_u(self, keypair: ElGamalKeyPair, nonce: ElementModQ, other: ElementModQ):
        proof = make_schnorr_proof(keypair, nonce)
        (k, h, u) = proof
        assume(other != u)
        proof2 = SchnorrProof(k, h, other)
        self.assertFalse(is_valid_schnorr_proof(proof2))

    @given(arb_elgamal_keypair(), arb_element_mod_q(), arb_element_mod_p())
    def test_schnorr_proofs_invalid_h(self, keypair: ElGamalKeyPair, nonce: ElementModQ, other: ElementModP):
        proof = make_schnorr_proof(keypair, nonce)
        (k, h, u) = proof
        assume(other != h)
        proof_bad = proof._replace(h=other)
        self.assertFalse(is_valid_schnorr_proof(proof_bad))

    @given(arb_elgamal_keypair(), arb_element_mod_q(), arb_element_mod_p_no_zero())
    def test_schnorr_proofs_invalid_public_key(self, keypair: ElGamalKeyPair, nonce: ElementModQ, other: ElementModP):
        proof = make_schnorr_proof(keypair, nonce)
        (k, h, u) = proof
        assume(other != k)
        proof2 = SchnorrProof(other, h, u)
        self.assertFalse(is_valid_schnorr_proof(proof2))

    @given(arb_elgamal_keypair(), arb_element_mod_q())
    def test_schnorr_proofs_bounds_checking(self, keypair: ElGamalKeyPair, nonce: ElementModQ):
        proof = make_schnorr_proof(keypair, nonce)
        (k, h, u) = proof
        proof2 = SchnorrProof(ZERO_MOD_P, h, u)
        proof3 = SchnorrProof(int_to_p_unchecked(P), h, u)
        self.assertFalse(is_valid_schnorr_proof(proof2))
        self.assertFalse(is_valid_schnorr_proof(proof3))
