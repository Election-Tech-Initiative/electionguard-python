from timeit import default_timer as timer
from hypothesis import given
from hypothesis.strategies import integers


from tests.base_test_case import BaseTestCase

from electionguard.constants import (
    get_generator,
    get_small_prime,
    get_large_prime,
)
from electionguard.elgamal import (
    ElGamalKeyPair,
    elgamal_encrypt,
    elgamal_add,
    elgamal_keypair_from_secret,
    elgamal_keypair_random,
    elgamal_combine_public_keys,
    hashed_elgamal_encrypt,
)
from electionguard.encrypt import ContestData
from electionguard.group import (
    ElementModQ,
    g_pow_p,
    ZERO_MOD_Q,
    TWO_MOD_Q,
    ONE_MOD_Q,
    ONE_MOD_P,
)
from electionguard.logs import log_info
from electionguard.nonces import Nonces
from electionguard.serialize import padded_decode
from electionguard.scheduler import Scheduler
from electionguard.utils import ContestErrorType, get_optional
from electionguard_tools.strategies.elgamal import elgamal_keypairs
from electionguard_tools.strategies.group import elements_mod_q_no_zero


class TestElGamal(BaseTestCase):
    """ElGamal tests"""

    def test_simple_elgamal_encryption_decryption(self) -> None:
        nonce = ONE_MOD_Q
        secret_key = TWO_MOD_Q
        keypair = get_optional(elgamal_keypair_from_secret(secret_key))
        public_key = keypair.public_key

        self.assertLess(public_key, get_large_prime())
        elem = g_pow_p(ZERO_MOD_Q)
        self.assertEqual(elem, ONE_MOD_P)  # g^0 == 1

        ciphertext = get_optional(elgamal_encrypt(0, nonce, keypair.public_key))
        self.assertEqual(get_generator(), ciphertext.pad)
        self.assertEqual(
            pow(ciphertext.pad.value, secret_key.value, get_large_prime()),
            pow(public_key.value, nonce.value, get_large_prime()),
        )
        self.assertEqual(
            ciphertext.data.value,
            pow(public_key.value, nonce.value, get_large_prime()),
        )

        plaintext = ciphertext.decrypt(keypair.secret_key)

        self.assertEqual(0, plaintext)

    @given(integers(0, 100), elgamal_keypairs())
    def test_elgamal_encrypt_requires_nonzero_nonce(
        self, message: int, keypair: ElGamalKeyPair
    ) -> None:
        self.assertEqual(None, elgamal_encrypt(message, ZERO_MOD_Q, keypair.public_key))

    def test_elgamal_keypair_from_secret_requires_key_greater_than_one(self) -> None:
        self.assertEqual(None, elgamal_keypair_from_secret(ZERO_MOD_Q))
        self.assertEqual(None, elgamal_keypair_from_secret(ONE_MOD_Q))

    @given(integers(0, 100), elements_mod_q_no_zero(), elgamal_keypairs())
    def test_elgamal_encryption_decryption_inverses(
        self, message: int, nonce: ElementModQ, keypair: ElGamalKeyPair
    ) -> None:
        ciphertext = get_optional(elgamal_encrypt(message, nonce, keypair.public_key))
        plaintext = ciphertext.decrypt(keypair.secret_key)

        self.assertEqual(message, plaintext)

    @given(integers(0, 100), elements_mod_q_no_zero(), elgamal_keypairs())
    def test_elgamal_encryption_decryption_with_known_nonce_inverses(
        self, message: int, nonce: ElementModQ, keypair: ElGamalKeyPair
    ) -> None:
        ciphertext = get_optional(elgamal_encrypt(message, nonce, keypair.public_key))
        plaintext = ciphertext.decrypt_known_nonce(keypair.public_key, nonce)

        self.assertEqual(message, plaintext)

    @given(elgamal_keypairs())
    def test_elgamal_generated_keypairs_are_within_range(
        self, keypair: ElGamalKeyPair
    ) -> None:
        self.assertLess(keypair.public_key, get_large_prime())
        self.assertLess(keypair.secret_key, get_small_prime())
        self.assertEqual(g_pow_p(keypair.secret_key), keypair.public_key)

    @given(
        elgamal_keypairs(),
        integers(0, 100),
        elements_mod_q_no_zero(),
        integers(0, 100),
        elements_mod_q_no_zero(),
    )
    def test_elgamal_add_homomorphic_accumulation_decrypts_successfully(
        self,
        keypair: ElGamalKeyPair,
        m1: int,
        r1: ElementModQ,
        m2: int,
        r2: ElementModQ,
    ) -> None:
        c1 = get_optional(elgamal_encrypt(m1, r1, keypair.public_key))
        c2 = get_optional(elgamal_encrypt(m2, r2, keypair.public_key))
        c_sum = elgamal_add(c1, c2)
        total = c_sum.decrypt(keypair.secret_key)

        self.assertEqual(total, m1 + m2)

    def test_elgamal_add_requires_args(self) -> None:
        self.assertRaises(Exception, elgamal_add)

    @given(elgamal_keypairs())
    def test_elgamal_keypair_produces_valid_residue(self, keypair) -> None:
        self.assertTrue(keypair.public_key.is_valid_residue())

    def test_elgamal_keypair_random(self) -> None:
        # Act
        random_keypair = elgamal_keypair_random()
        random_keypair_two = elgamal_keypair_random()

        # Assert
        self.assertIsNotNone(random_keypair)
        self.assertIsNotNone(random_keypair.public_key)
        self.assertIsNotNone(random_keypair.secret_key)
        self.assertNotEqual(random_keypair, random_keypair_two)

    def test_elgamal_combine_public_keys(self) -> None:
        # Arrange
        random_keypair = elgamal_keypair_random()
        random_keypair_two = elgamal_keypair_random()
        public_keys = [random_keypair.public_key, random_keypair_two.public_key]

        # Act
        joint_key = elgamal_combine_public_keys(public_keys)

        # Assert
        self.assertIsNotNone(joint_key)
        self.assertNotEqual(joint_key, random_keypair.public_key)
        self.assertNotEqual(joint_key, random_keypair_two.public_key)

    def test_gmpy2_parallelism_is_safe(self) -> None:
        """
        Ensures running lots of parallel exponentiations still yields the correct answer.
        This verifies that nothing incorrect is happening in the GMPY2 library
        """

        # Arrange
        scheduler = Scheduler()
        problem_size = 1000
        random_secret_keys = Nonces(ElementModQ(3))[0:problem_size]
        log_info(
            f"testing GMPY2 powmod parallelism safety (cpus = {scheduler.cpu_count}, problem_size = {problem_size})"
        )

        # Act
        start = timer()
        keypairs = scheduler.schedule(
            elgamal_keypair_from_secret,
            [list([secret_key]) for secret_key in random_secret_keys],
        )
        end1 = timer()

        # Assert
        for keypair in keypairs:
            self.assertEqual(
                keypair.public_key,
                elgamal_keypair_from_secret(keypair.secret_key).public_key,
            )
        end2 = timer()
        scheduler.close()
        log_info(f"Parallelism speedup: {(end2 - end1) / (end1 - start):.3f}")

    def test_hashed_elgamal_encryption(self) -> None:
        """
        Ensure Hashed ElGamal encrypts and decrypts as expected.
        """

        # Arrange
        message = ContestData(ContestErrorType.Default)
        keypair = elgamal_keypair_random()
        nonce = ONE_MOD_Q
        seed = ONE_MOD_Q

        # Act
        padded_message = message.to_bytes()
        encrypted_message = hashed_elgamal_encrypt(
            padded_message, nonce, keypair.public_key, seed
        )
        decrypted_message = encrypted_message.decrypt(keypair.secret_key, seed)
        if decrypted_message is not None:
            unpadded_message = padded_decode(ContestData, decrypted_message)

        # Assert
        self.assertIsNotNone(encrypted_message)
        self.assertIsNotNone(decrypted_message)
        if decrypted_message is not None:
            self.assertEqual(padded_message, decrypted_message)
            self.assertEqual(message, unpadded_message)
