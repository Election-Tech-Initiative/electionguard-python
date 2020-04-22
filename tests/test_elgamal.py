import unittest
from multiprocessing import Pool, cpu_count
from timeit import default_timer as timer

from hypothesis import given
from hypothesis.strategies import integers

from electionguard.elgamal import (
    ElGamalKeyPair,
    elgamal_encrypt,
    elgamal_add,
    elgamal_keypair_from_secret,
)
from electionguard.group import (
    ElementModQ,
    g_pow_p,
    G,
    Q,
    P,
    ZERO_MOD_Q,
    TWO_MOD_Q,
    ONE_MOD_Q,
    ONE_MOD_P,
    int_to_q,
    unwrap_optional,
    int_to_q_unchecked,
)
from electionguard.logs import log_info
from electionguard.nonces import Nonces
from electionguardtest.elgamal import arb_elgamal_keypair
from tests.test_group import arb_element_mod_q_no_zero, arb_element_mod_q


class TestElGamal(unittest.TestCase):
    def test_simple_elgamal_encryption_decryption(self):
        nonce = ONE_MOD_Q
        secret_key = TWO_MOD_Q
        keypair = unwrap_optional(elgamal_keypair_from_secret(secret_key))
        public_key = keypair.public_key

        self.assertLess(public_key.to_int(), P)
        elem = g_pow_p(ZERO_MOD_Q)
        self.assertEqual(elem, ONE_MOD_P)  # g^0 == 1

        ciphertext = unwrap_optional(elgamal_encrypt(0, nonce, keypair.public_key))
        self.assertEqual(G, ciphertext.alpha.to_int())
        self.assertEqual(
            pow(ciphertext.alpha.to_int(), secret_key.to_int(), P),
            pow(public_key.to_int(), nonce.to_int(), P),
        )
        self.assertEqual(
            ciphertext.beta.to_int(), pow(public_key.to_int(), nonce.to_int(), P),
        )

        plaintext = ciphertext.decrypt(keypair.secret_key)

        self.assertEqual(0, plaintext)

    @given(integers(0, 100), arb_elgamal_keypair())
    def test_elgamal_encrypt_requires_nonzero_nonce(
        self, message: int, keypair: ElGamalKeyPair
    ):
        self.assertEqual(None, elgamal_encrypt(message, ZERO_MOD_Q, keypair.public_key))

    def test_elgamal_keypair_from_secret_requires_key_greater_than_one(self):
        self.assertEqual(None, elgamal_keypair_from_secret(ZERO_MOD_Q))
        self.assertEqual(None, elgamal_keypair_from_secret(ONE_MOD_Q))

    @given(integers(0, 100), arb_element_mod_q_no_zero(), arb_elgamal_keypair())
    def test_elgamal_encryption_decryption_inverses(
        self, message: int, nonce: ElementModQ, keypair: ElGamalKeyPair
    ):
        ciphertext = unwrap_optional(
            elgamal_encrypt(message, nonce, keypair.public_key)
        )
        plaintext = ciphertext.decrypt(keypair.secret_key)

        self.assertEqual(message, plaintext)

    @given(integers(0, 100), arb_element_mod_q_no_zero(), arb_elgamal_keypair())
    def test_elgamal_encryption_decryption_with_known_nonce_inverses(
        self, message: int, nonce: ElementModQ, keypair: ElGamalKeyPair
    ):
        ciphertext = unwrap_optional(
            elgamal_encrypt(message, nonce, keypair.public_key)
        )
        plaintext = ciphertext.decrypt_known_nonce(keypair.public_key, nonce)

        self.assertEqual(message, plaintext)

    @given(arb_elgamal_keypair())
    def test_elgamal_generated_keypairs_are_within_range(self, keypair: ElGamalKeyPair):
        self.assertLess(keypair.public_key.to_int(), P)
        self.assertLess(keypair.secret_key.to_int(), G)
        self.assertEqual(g_pow_p(keypair.secret_key), keypair.public_key)

    @given(
        arb_elgamal_keypair(),
        integers(0, 100),
        arb_element_mod_q_no_zero(),
        integers(0, 100),
        arb_element_mod_q_no_zero(),
    )
    def test_elgamal_add_homomorphic_accumulation_decrypts_successfully(
        self,
        keypair: ElGamalKeyPair,
        m1: int,
        r1: ElementModQ,
        m2: int,
        r2: ElementModQ,
    ):
        c1 = unwrap_optional(elgamal_encrypt(m1, r1, keypair.public_key))
        c2 = unwrap_optional(elgamal_encrypt(m2, r2, keypair.public_key))
        c_sum = elgamal_add(c1, c2)
        total = c_sum.decrypt(keypair.secret_key)

        self.assertEqual(total, m1 + m2)

    def test_elgamal_add_requires_args(self):
        self.assertRaises(Exception, elgamal_add)

    @given(arb_elgamal_keypair())
    def test_elgamal_keypair_produces_valid_residue(self, keypair):
        self.assertTrue(keypair.public_key.is_valid_residue())

    # Here's an oddball test: checking whether running lots of parallel exponentiations yields the
    # correct answer. It certainly *should* work, but this verifies that nothing weird is happening
    # in the GMPY2 library, with it's C code below that.
    def test_gmpy2_parallelism_is_safe(self):
        cpus = cpu_count()
        problem_size = 1000
        secret_keys = Nonces(int_to_q_unchecked(3))[
            0:problem_size
        ]  # list of 1000 might-as-well-be-random Q's
        log_info(
            f"testing GMPY2 powmod parallelism safety (cpus = {cpus}, problem_size = {problem_size})"
        )

        # compute in parallel
        start = timer()
        p = Pool(cpus)
        keypairs = p.map(elgamal_keypair_from_secret, secret_keys)
        end1 = timer()

        # verify scalar
        for keypair in keypairs:
            self.assertEqual(
                keypair.public_key,
                elgamal_keypair_from_secret(keypair.secret_key).public_key,
            )
        end2 = timer()
        p.close()  # apparently necessary to avoid warnings from the Pool system
        log_info(f"Parallelism speedup: {(end2 - end1) / (end1 - start):.3f}")
