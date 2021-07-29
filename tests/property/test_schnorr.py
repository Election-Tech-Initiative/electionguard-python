from hypothesis import given, assume

from tests.base_test_case import BaseTestCase
from tests.property.test_elgamal import elgamal_keypairs
from tests.property.test_group import (
    elements_mod_q,
    elements_mod_p_no_zero,
    elements_mod_p,
)

from electionguard.constants import get_large_prime
from electionguard.elgamal import ElGamalKeyPair, elgamal_keypair_from_secret
from electionguard.group import (
    ElementModQ,
    ElementModP,
    ZERO_MOD_P,
    TWO_MOD_Q,
    ONE_MOD_Q,
)
from electionguard.schnorr import (
    make_schnorr_proof,
    SchnorrProof,
)
from electionguard.utils import get_optional


class TestSchnorr(BaseTestCase):
    """Schnorr tests"""

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
        assume(other != proof.response)
        proof2 = SchnorrProof(
            proof.public_key, proof.commitment, proof.challenge, other
        )
        self.assertFalse(proof2.is_valid())

    @given(elgamal_keypairs(), elements_mod_q(), elements_mod_p())
    def test_schnorr_proofs_invalid_h(
        self, keypair: ElGamalKeyPair, nonce: ElementModQ, other: ElementModP
    ) -> None:
        proof = make_schnorr_proof(keypair, nonce)
        assume(other != proof.commitment)
        proof_bad = SchnorrProof(
            proof.public_key, other, proof.challenge, proof.response
        )
        self.assertFalse(proof_bad.is_valid())

    @given(elgamal_keypairs(), elements_mod_q(), elements_mod_p_no_zero())
    def test_schnorr_proofs_invalid_public_key(
        self, keypair: ElGamalKeyPair, nonce: ElementModQ, other: ElementModP
    ) -> None:
        proof = make_schnorr_proof(keypair, nonce)
        assume(other != proof.public_key)
        proof2 = SchnorrProof(other, proof.commitment, proof.challenge, proof.response)
        self.assertFalse(proof2.is_valid())

    @given(elgamal_keypairs(), elements_mod_q())
    def test_schnorr_proofs_bounds_checking(
        self, keypair: ElGamalKeyPair, nonce: ElementModQ
    ) -> None:
        proof = make_schnorr_proof(keypair, nonce)
        proof2 = SchnorrProof(
            ZERO_MOD_P, proof.commitment, proof.challenge, proof.response
        )
        proof3 = SchnorrProof(
            ElementModP(get_large_prime(), False),
            proof.commitment,
            proof.challenge,
            proof.response,
        )
        self.assertFalse(proof2.is_valid())
        self.assertFalse(proof3.is_valid())
