from datetime import timedelta
from unittest import TestCase

from hypothesis import given, settings, HealthCheck
from hypothesis.strategies import integers

from electionguard.chaum_pedersen import (
    ConstantChaumPedersenProof,
    make_disjunctive_chaum_pedersen_zero,
    make_disjunctive_chaum_pedersen_one,
    make_chaum_pedersen,
    make_constant_chaum_pedersen,
    make_disjunctive_chaum_pedersen,
    make_chaum_pedersen_generic,
)
from electionguard.elgamal import (
    ElGamalKeyPair,
    elgamal_encrypt,
    elgamal_keypair_from_secret,
)
from electionguard.group import (
    ElementModQ,
    TWO_MOD_Q,
    ONE_MOD_Q,
    int_to_p,
    ElementModP,
    pow_p,
    int_to_q,
    add_q,
    ONE_MOD_P,
    TWO_MOD_P,
)
from electionguard.utils import get_optional
from electionguardtest.elgamal import elgamal_keypairs
from electionguardtest.group import (
    elements_mod_q_no_zero,
    elements_mod_q,
    elements_mod_p_no_zero,
)


class TestDisjunctiveChaumPedersen(TestCase):
    def test_djcp_proofs_simple(self):
        # doesn't get any simpler than this
        keypair = elgamal_keypair_from_secret(TWO_MOD_Q)
        nonce = ONE_MOD_Q
        seed = TWO_MOD_Q
        message0 = get_optional(elgamal_encrypt(0, nonce, keypair.public_key))
        proof0 = make_disjunctive_chaum_pedersen_zero(
            message0, nonce, keypair.public_key, ONE_MOD_Q, seed
        )
        proof0bad = make_disjunctive_chaum_pedersen_one(
            message0, nonce, keypair.public_key, ONE_MOD_Q, seed
        )
        self.assertTrue(proof0.is_valid(message0, keypair.public_key, ONE_MOD_Q))
        self.assertFalse(proof0bad.is_valid(message0, keypair.public_key, ONE_MOD_Q))

        message1 = get_optional(elgamal_encrypt(1, nonce, keypair.public_key))
        proof1 = make_disjunctive_chaum_pedersen_one(
            message1, nonce, keypair.public_key, ONE_MOD_Q, seed
        )
        proof1bad = make_disjunctive_chaum_pedersen_zero(
            message1, nonce, keypair.public_key, ONE_MOD_Q, seed
        )
        self.assertTrue(proof1.is_valid(message1, keypair.public_key, ONE_MOD_Q))
        self.assertFalse(proof1bad.is_valid(message1, keypair.public_key, ONE_MOD_Q))

    def test_djcp_proof_invalid_inputs(self):
        # this is here to push up our coverage
        keypair = elgamal_keypair_from_secret(TWO_MOD_Q)
        nonce = ONE_MOD_Q
        seed = TWO_MOD_Q
        message0 = get_optional(elgamal_encrypt(0, nonce, keypair.public_key))
        self.assertRaises(
            Exception,
            make_disjunctive_chaum_pedersen,
            message0,
            nonce,
            keypair.public_key,
            seed,
            3,
        )

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(elgamal_keypairs(), elements_mod_q_no_zero(), elements_mod_q())
    def test_djcp_proof_zero(
        self, keypair: ElGamalKeyPair, nonce: ElementModQ, seed: ElementModQ
    ):
        message = get_optional(elgamal_encrypt(0, nonce, keypair.public_key))
        proof = make_disjunctive_chaum_pedersen_zero(
            message, nonce, keypair.public_key, ONE_MOD_Q, seed
        )
        proof_bad = make_disjunctive_chaum_pedersen_one(
            message, nonce, keypair.public_key, ONE_MOD_Q, seed
        )
        self.assertTrue(proof.is_valid(message, keypair.public_key, ONE_MOD_Q))
        self.assertFalse(proof_bad.is_valid(message, keypair.public_key, ONE_MOD_Q))

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(elgamal_keypairs(), elements_mod_q_no_zero(), elements_mod_q())
    def test_djcp_proof_one(
        self, keypair: ElGamalKeyPair, nonce: ElementModQ, seed: ElementModQ
    ):
        message = get_optional(elgamal_encrypt(1, nonce, keypair.public_key))
        proof = make_disjunctive_chaum_pedersen_one(
            message, nonce, keypair.public_key, ONE_MOD_Q, seed
        )
        proof_bad = make_disjunctive_chaum_pedersen_zero(
            message, nonce, keypair.public_key, ONE_MOD_Q, seed
        )
        self.assertTrue(proof.is_valid(message, keypair.public_key, ONE_MOD_Q))
        self.assertFalse(proof_bad.is_valid(message, keypair.public_key, ONE_MOD_Q))

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(elgamal_keypairs(), elements_mod_q_no_zero(), elements_mod_q())
    def test_djcp_proof_broken(
        self, keypair: ElGamalKeyPair, nonce: ElementModQ, seed: ElementModQ
    ):
        # verify two different ways to generate an invalid C-P proof.
        message = get_optional(elgamal_encrypt(0, nonce, keypair.public_key))
        message_bad = get_optional(elgamal_encrypt(2, nonce, keypair.public_key))
        proof = make_disjunctive_chaum_pedersen_zero(
            message, nonce, keypair.public_key, ONE_MOD_Q, seed
        )
        proof_bad = make_disjunctive_chaum_pedersen_zero(
            message_bad, nonce, keypair.public_key, ONE_MOD_Q, seed
        )

        self.assertFalse(proof_bad.is_valid(message_bad, keypair.public_key, ONE_MOD_Q))
        self.assertFalse(proof.is_valid(message_bad, keypair.public_key, ONE_MOD_Q))


class TestChaumPedersen(TestCase):
    def test_cp_proofs_simple(self):
        keypair = elgamal_keypair_from_secret(TWO_MOD_Q)
        nonce = ONE_MOD_Q
        seed = TWO_MOD_Q
        message = get_optional(elgamal_encrypt(0, nonce, keypair.public_key))
        decryption = message.partial_decrypt(keypair.secret_key)
        proof = make_chaum_pedersen(
            message, keypair.secret_key, decryption, seed, ONE_MOD_Q
        )
        bad_proof = make_chaum_pedersen(
            message, keypair.secret_key, TWO_MOD_Q, seed, ONE_MOD_Q
        )
        self.assertTrue(
            proof.is_valid(message, keypair.public_key, decryption, ONE_MOD_Q)
        )
        self.assertFalse(
            bad_proof.is_valid(message, keypair.public_key, decryption, ONE_MOD_Q)
        )

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(
        elgamal_keypairs(),
        elements_mod_q_no_zero(),
        elements_mod_q(),
        integers(0, 100),
        integers(0, 100),
    )
    def test_cp_proof(
        self,
        keypair: ElGamalKeyPair,
        nonce: ElementModQ,
        seed: ElementModQ,
        constant: int,
        bad_constant: int,
    ):
        if constant == bad_constant:
            bad_constant = constant + 1

        message = get_optional(elgamal_encrypt(constant, nonce, keypair.public_key))
        decryption = message.partial_decrypt(keypair.secret_key)
        proof = make_chaum_pedersen(
            message, keypair.secret_key, decryption, seed, ONE_MOD_Q
        )
        bad_proof = make_chaum_pedersen(
            message, keypair.secret_key, int_to_p(bad_constant), seed, ONE_MOD_Q
        )
        self.assertTrue(
            proof.is_valid(message, keypair.public_key, decryption, ONE_MOD_Q)
        )
        self.assertFalse(
            bad_proof.is_valid(message, keypair.public_key, decryption, ONE_MOD_Q)
        )


class TestConstantChaumPedersen(TestCase):
    def test_ccp_proofs_simple_encryption_of_zero(self):
        keypair = elgamal_keypair_from_secret(TWO_MOD_Q)
        nonce = ONE_MOD_Q
        seed = TWO_MOD_Q
        message = get_optional(elgamal_encrypt(0, nonce, keypair.public_key))
        proof = make_constant_chaum_pedersen(
            message, 0, nonce, keypair.public_key, seed, ONE_MOD_Q
        )
        bad_proof = make_constant_chaum_pedersen(
            message, 1, nonce, keypair.public_key, seed, ONE_MOD_Q
        )
        self.assertTrue(proof.is_valid(message, keypair.public_key, ONE_MOD_Q))
        self.assertFalse(bad_proof.is_valid(message, keypair.public_key, ONE_MOD_Q))

    def test_ccp_proofs_simple_encryption_of_one(self):
        keypair = elgamal_keypair_from_secret(TWO_MOD_Q)
        nonce = ONE_MOD_Q
        seed = TWO_MOD_Q
        message = get_optional(elgamal_encrypt(1, nonce, keypair.public_key))
        proof = make_constant_chaum_pedersen(
            message, 1, nonce, keypair.public_key, seed, ONE_MOD_Q
        )
        bad_proof = make_constant_chaum_pedersen(
            message, 0, nonce, keypair.public_key, seed, ONE_MOD_Q
        )
        self.assertTrue(proof.is_valid(message, keypair.public_key, ONE_MOD_Q))
        self.assertFalse(bad_proof.is_valid(message, keypair.public_key, ONE_MOD_Q))

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(
        elgamal_keypairs(),
        elements_mod_q_no_zero(),
        elements_mod_q(),
        integers(0, 100),
        integers(0, 100),
    )
    def test_ccp_proof(
        self,
        keypair: ElGamalKeyPair,
        nonce: ElementModQ,
        seed: ElementModQ,
        constant: int,
        bad_constant: int,
    ):
        # assume() slows down the test-case generation
        # so assume(constant != bad_constant)
        if constant == bad_constant:
            bad_constant = constant + 1

        message = get_optional(elgamal_encrypt(constant, nonce, keypair.public_key))
        message_bad = get_optional(
            elgamal_encrypt(bad_constant, nonce, keypair.public_key)
        )

        proof = make_constant_chaum_pedersen(
            message, constant, nonce, keypair.public_key, seed, ONE_MOD_Q
        )
        self.assertTrue(proof.is_valid(message, keypair.public_key, ONE_MOD_Q))

        proof_bad1 = make_constant_chaum_pedersen(
            message_bad, constant, nonce, keypair.public_key, seed, ONE_MOD_Q
        )
        self.assertFalse(
            proof_bad1.is_valid(message_bad, keypair.public_key, ONE_MOD_Q)
        )

        proof_bad2 = make_constant_chaum_pedersen(
            message, bad_constant, nonce, keypair.public_key, seed, ONE_MOD_Q
        )
        self.assertFalse(proof_bad2.is_valid(message, keypair.public_key, ONE_MOD_Q))

        proof_bad3 = ConstantChaumPedersenProof(
            proof.pad, proof.data, proof.challenge, proof.response, -1
        )
        self.assertFalse(proof_bad3.is_valid(message, keypair.public_key, ONE_MOD_Q))


class TestGenericChaumPedersen(TestCase):
    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(
        elements_mod_p_no_zero(),
        elements_mod_p_no_zero(),
        elements_mod_q_no_zero(),
        elements_mod_q_no_zero(),
        elements_mod_q(),
    )
    def test_gcp_proof(
        self,
        g: ElementModP,
        h: ElementModP,
        x: ElementModQ,
        notx: ElementModQ,
        seed: ElementModQ,
    ):
        # simple/fast way to exclude bad values for g, h, and x
        # - we need g and h to be at least two, otherwise degeneracies
        # - we need x != notx, since that's kind of the whole idea
        if g == ONE_MOD_P:
            g = TWO_MOD_P
        if h == ONE_MOD_P:
            h = TWO_MOD_P
        if x == notx:
            notx = add_q(x, 1)

        gx = pow_p(g, x)
        hx = pow_p(h, x)
        gnotx = pow_p(g, notx)
        hnotx = pow_p(h, notx)
        proof = make_chaum_pedersen_generic(g, h, x, seed)
        self.assertTrue(proof.is_valid(g, gx, h, hx))
        self.assertFalse(proof.is_valid(g, gnotx, h, hx))
        self.assertFalse(proof.is_valid(g, gx, h, hnotx))
        self.assertFalse(proof.is_valid(g, gnotx, h, hnotx))

    def test_gcp_proof_simple(self):
        g = int_to_p(2)
        h = int_to_p(3)
        x = int_to_q(5)
        notx = int_to_q(2)
        seed = int_to_q(0)

        gx = pow_p(g, x)
        hx = pow_p(h, x)
        gnotx = pow_p(g, notx)
        hnotx = pow_p(h, notx)

        proof = make_chaum_pedersen_generic(g, h, x, seed)
        self.assertTrue(proof.is_valid(g, gx, h, hx))
        self.assertFalse(proof.is_valid(g, gnotx, h, hx))
        self.assertFalse(proof.is_valid(g, gx, h, hnotx))
        self.assertFalse(proof.is_valid(g, gnotx, h, hnotx))
