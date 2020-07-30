import unittest

from hypothesis import given, assume

from electionguard.elgamal import ElGamalKeyPair, elgamal_keypair_from_secret
from electionguard.group import (
    ElementModQ,
    ElementModP,
    ZERO_MOD_P,
    P,
    int_to_p_unchecked,
    TWO_MOD_Q,
    ONE_MOD_Q,
)
from electionguard.schnorr import (
    make_schnorr_proof,
    SchnorrProof,
)
from electionguard.utils import get_optional
from tests.test_elgamal import elgamal_keypairs
from tests.test_group import (
    elements_mod_q,
    elements_mod_p_no_zero,
    elements_mod_p,
)


class TestSchnorr(unittest.TestCase):
    def test_schnorr_proofs_simple(self) -> None:
        # doesn't get any simpler than this
        keypair = get_optional(elgamal_keypair_from_secret(TWO_MOD_Q))
        nonce = ONE_MOD_Q
        proof = make_schnorr_proof(keypair, nonce)
        self.assertTrue(proof.is_valid())

    @given(elgamal_keypairs(), elements_mod_q())
    def test_schnorr_proofs_valid(
        self, keypair: ElGamalKeyPair, nonce: ElementModQ
    ) -> None:
        proof = make_schnorr_proof(keypair, nonce)
        self.assertTrue(proof.is_valid())

    # Now, we introduce errors in the proofs and make sure that they fail to verify
    @given(elgamal_keypairs(), elements_mod_q(), elements_mod_q())
    def test_schnorr_proofs_invalid_u(
        self, keypair: ElGamalKeyPair, nonce: ElementModQ, other: ElementModQ
    ) -> None:
        proof = make_schnorr_proof(keypair, nonce)
        assume(other != proof.u)
        proof2 = SchnorrProof(proof.k, proof.h, other)
        self.assertFalse(proof2.is_valid())

    @given(elgamal_keypairs(), elements_mod_q(), elements_mod_p())
    def test_schnorr_proofs_invalid_h(
        self, keypair: ElGamalKeyPair, nonce: ElementModQ, other: ElementModP
    ) -> None:
        proof = make_schnorr_proof(keypair, nonce)
        assume(other != proof.h)
        proof_bad = SchnorrProof(proof.k, other, proof.u)
        self.assertFalse(proof_bad.is_valid())

    @given(elgamal_keypairs(), elements_mod_q(), elements_mod_p_no_zero())
    def test_schnorr_proofs_invalid_public_key(
        self, keypair: ElGamalKeyPair, nonce: ElementModQ, other: ElementModP
    ) -> None:
        proof = make_schnorr_proof(keypair, nonce)
        assume(other != proof.k)
        proof2 = SchnorrProof(other, proof.h, proof.u)
        self.assertFalse(proof2.is_valid())

    @given(elgamal_keypairs(), elements_mod_q())
    def test_schnorr_proofs_bounds_checking(
        self, keypair: ElGamalKeyPair, nonce: ElementModQ
    ) -> None:
        proof = make_schnorr_proof(keypair, nonce)
        proof2 = SchnorrProof(ZERO_MOD_P, proof.h, proof.u)
        proof3 = SchnorrProof(int_to_p_unchecked(P), proof.h, proof.u)
        self.assertFalse(proof2.is_valid())
        self.assertFalse(proof3.is_valid())
