import unittest

from hypothesis import given
from hypothesis.strategies import composite, integers

from electionguard.elgamal import ElGamalKeyPair, _message_to_element, elgamal_encrypt, elgamal_decrypt, \
    elgamal_decrypt_known_nonce, \
    elgamal_add, elgamal_keypair_from_secret
from electionguard.group import ElementModQ, g_pow_p, G, Q, P, valid_residue, ZERO_MOD_Q, TWO_MOD_Q, ONE_MOD_Q, \
    ONE_MOD_P, elem_to_int
from tests.test_group import arb_element_mod_q_no_zero, arb_element_mod_q


@composite
def arb_elgamal_keypair(draw, elem=arb_element_mod_q_no_zero().filter(lambda x: elem_to_int(x) > 1)):
    """
    Generates an arbitrary ElGamal secret/public keypair.
    """
    return elgamal_keypair_from_secret(draw(elem))


class TestElGamal(unittest.TestCase):
    def test_encryption_decryption_simplistic(self):
        nonce = ONE_MOD_Q
        secret_key = TWO_MOD_Q
        keypair = elgamal_keypair_from_secret(secret_key)
        public_key = keypair.public_key

        self.assertLess(elem_to_int(public_key), P)
        elem = _message_to_element(0)
        self.assertEqual(elem, ONE_MOD_P)  # g^0 == 1

        ciphertext = elgamal_encrypt(0, nonce, keypair.public_key)
        self.assertEqual(G, elem_to_int(ciphertext.alpha))
        self.assertEqual(pow(elem_to_int(ciphertext.alpha), elem_to_int(secret_key), P),
                         pow(elem_to_int(public_key), elem_to_int(nonce), P))
        self.assertEqual(elem_to_int(ciphertext.beta),
                         pow(elem_to_int(public_key), elem_to_int(nonce), P))

        plaintext = elgamal_decrypt(ciphertext, keypair.secret_key)

        self.assertEqual(0, plaintext)

    @given(integers(0, 100), arb_elgamal_keypair())
    def test_elgamal_requires_nonzero_nonce(self, message: int, keypair: ElGamalKeyPair):
        self.assertRaises(Exception, elgamal_encrypt, message, ZERO_MOD_Q, keypair.public_key)

    def test_elgamal_requires_secret_key_greater_than_one(self):
        self.assertRaises(Exception, elgamal_keypair_from_secret, ZERO_MOD_Q)
        self.assertRaises(Exception, elgamal_keypair_from_secret, ONE_MOD_Q)

    @given(integers(0, 100), arb_element_mod_q_no_zero(), arb_elgamal_keypair())
    def test_encryption_decryption_inverses(self, message: int, nonce: ElementModQ, keypair: ElGamalKeyPair):
        ciphertext = elgamal_encrypt(message, nonce, keypair.public_key)
        plaintext = elgamal_decrypt(ciphertext, keypair.secret_key)

        self.assertEqual(message, plaintext)

    @given(integers(0, 100), arb_element_mod_q_no_zero(), arb_elgamal_keypair())
    def test_encryption_decryption_inverses2(self, message: int, nonce: ElementModQ, keypair: ElGamalKeyPair):
        ciphertext = elgamal_encrypt(message, nonce, keypair.public_key)
        plaintext = elgamal_decrypt_known_nonce(ciphertext, keypair.public_key, nonce)

        self.assertEqual(message, plaintext)

    @given(arb_element_mod_q())
    def test_large_values_rejected_by_message_to_element(self, q: ElementModQ):
        oversize = elem_to_int(q) + Q
        self.assertRaises(Exception, _message_to_element, oversize)

    @given(arb_elgamal_keypair())
    def test_elgamal_keypairs_are_sane(self, keypair: ElGamalKeyPair):
        self.assertLess(elem_to_int(keypair.public_key), P)
        self.assertLess(elem_to_int(keypair.secret_key), G)
        self.assertEqual(g_pow_p(keypair.secret_key), keypair.public_key)

    @given(arb_elgamal_keypair(), integers(0, 100), arb_element_mod_q_no_zero(), integers(0, 100),
           arb_element_mod_q_no_zero())
    def test_elgamal_homomorphic_accumulation(self, keypair: ElGamalKeyPair, m1: int, r1: ElementModQ, m2: int,
                                              r2: ElementModQ):
        c1 = elgamal_encrypt(m1, r1, keypair.public_key)
        c2 = elgamal_encrypt(m2, r2, keypair.public_key)
        c_sum = elgamal_add(c1, c2)
        total = elgamal_decrypt(c_sum, keypair.secret_key)

        self.assertEqual(total, m1 + m2)

    @given(arb_elgamal_keypair())
    def test_elgamal_keys_valid_residue(self, keypair):
        self.assertTrue(valid_residue(keypair.public_key))
