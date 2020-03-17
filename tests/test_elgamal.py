import unittest

from hypothesis import given
from hypothesis.strategies import composite, integers

from electionguard.elgamal import ElGamalKeyPair, _message_to_element, encrypt, decrypt, decrypt_known_nonce, \
    elgamal_add
from electionguard.group import ElementModQ, g_pow, G, Q, P, valid_residue, ZERO_MOD_Q
from tests.test_group import arb_element_mod_q_no_zero, arb_element_mod_q


@composite
def arb_elgamal_keypair(draw, elem=arb_element_mod_q_no_zero().filter(lambda x: x.elem > 1)):
    """
    Generates an arbitrary ElGamal secret/public keypair.
    """
    secret_key = draw(elem)
    return ElGamalKeyPair(secret_key, g_pow(secret_key))


class TestElGamal(unittest.TestCase):
    def test_encryption_decryption_simplistic(self):
        message = ElementModQ(0)
        nonce = ElementModQ(1)
        secret_key = ElementModQ(2)
        public_key = g_pow(secret_key)
        self.assertLess(public_key.elem, P)

        keypair = ElGamalKeyPair(secret_key, public_key)
        elem = _message_to_element(message.elem)
        self.assertEqual(elem.elem, 1)  # g^0 == 1

        ciphertext = encrypt(0, nonce, keypair.public_key)
        self.assertEqual(G, ciphertext.alpha.elem)
        self.assertEqual(pow(ciphertext.alpha.elem, secret_key.elem, P), pow(public_key.elem, nonce.elem, P))
        self.assertEqual(ciphertext.beta.elem, pow(public_key.elem, nonce.elem, P))

        plaintext = decrypt(ciphertext, keypair.secret_key)

        self.assertEqual(0, plaintext)

    @given(integers(0, 100), arb_elgamal_keypair())
    def test_elgamal_requires_nonzero_nonce(self, message: int, keypair: ElGamalKeyPair):
        self.assertRaises(Exception, encrypt, message, ZERO_MOD_Q, keypair.public_key)

    @given(integers(0, 100), arb_element_mod_q_no_zero(), arb_elgamal_keypair())
    def test_encryption_decryption_inverses(self, message: int, nonce: ElementModQ, keypair: ElGamalKeyPair):
        ciphertext = encrypt(message, nonce, keypair.public_key)
        plaintext = decrypt(ciphertext, keypair.secret_key)

        self.assertEqual(message, plaintext)

    @given(integers(0, 100), arb_element_mod_q_no_zero(), arb_elgamal_keypair())
    def test_encryption_decryption_inverses2(self, message: int, nonce: ElementModQ, keypair: ElGamalKeyPair):
        ciphertext = encrypt(message, nonce, keypair.public_key)
        plaintext = decrypt_known_nonce(ciphertext, keypair.public_key, nonce)

        self.assertEqual(message, plaintext)

    @given(arb_element_mod_q())
    def test_large_values_rejected_by_message_to_element(self, q: ElementModQ):
        oversize = q.elem + Q
        self.assertRaises(Exception, _message_to_element, oversize)

    @given(arb_elgamal_keypair())
    def test_elgamal_keypairs_are_sane(self, keypair: ElGamalKeyPair):
        self.assertLess(keypair.public_key.elem, P)
        self.assertLess(keypair.secret_key.elem, G)
        self.assertEqual(g_pow(keypair.secret_key), keypair.public_key)

    @given(arb_elgamal_keypair(), integers(0, 100), arb_element_mod_q_no_zero(), integers(0, 100),
           arb_element_mod_q_no_zero())
    def test_elgamal_homomorphic_accumulation(self, keypair: ElGamalKeyPair, m1: int, r1: ElementModQ, m2: int,
                                              r2: ElementModQ):
        c1 = encrypt(m1, r1, keypair.public_key)
        c2 = encrypt(m2, r2, keypair.public_key)
        c_sum = elgamal_add(c1, c2)
        total = decrypt(c_sum, keypair.secret_key)

        self.assertEqual(total, m1 + m2)

    @given(arb_elgamal_keypair())
    def test_elgamal_keys_valid_residue(self, keypair):
        self.assertTrue(valid_residue(keypair.public_key))
