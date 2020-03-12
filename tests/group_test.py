import unittest
from hypothesis import given, strategies as st
from hypothesis.strategies import composite
from electionguard.group import P, Q, ElementModP, ElementModQ, ElGamalKeyPair, g_pow, message_to_element, encrypt, \
    decrypt, decrypt_known_nonce, mult_inv_p, ONE_MOD_P, mult_mod_p, ZERO_MOD_P


@composite
def arb_element_mod_q(draw, elem=st.integers(min_value=0, max_value=Q-1)):
    """
    Generates an arbitrary element from [0,Q).
    """
    return ElementModQ(draw(elem))


@composite
def arb_element_mod_q_no_zero(draw, elem=st.integers(min_value=1, max_value=Q-1)):
    """
    Generates an arbitrary element from [1,Q).
    """
    return ElementModQ(draw(elem))


@composite
def arb_element_mod_p(draw, elem=st.integers(min_value=0, max_value=P-1)):
    """
    Generates an arbitrary element from [0,P).
    """
    return ElementModP(draw(elem))


@composite
def arb_element_mod_p_no_zero(draw, elem=st.integers(min_value=1, max_value=P-1)):
    """
    Generates an arbitrary element from [1,P).
    """
    return ElementModP(draw(elem))


@composite
def arb_elgamal_keypair(draw, elem=arb_element_mod_q_no_zero()):
    """
    Generates an arbitrary ElGamal secret/public keypair.
    """
    secret_key = draw(elem)
    return ElGamalKeyPair(secret_key, g_pow(secret_key))


# Simple tests that ElGamal satisfies its various inverse and homomorphic properties
# will also exercise the library in general.

class TestElGamal(unittest.TestCase):
    @given(arb_element_mod_q(), arb_element_mod_q(), arb_elgamal_keypair())
    def test_encryption_decryption_inverses(self, message: ElementModQ, nonce: ElementModQ, keypair: ElGamalKeyPair):
        elem = message_to_element(message.elem)
        ciphertext = encrypt(elem, nonce, keypair.public_key)
        plaintext = decrypt(ciphertext, keypair.secret_key)

        self.assertEqual(elem, plaintext)

    @given(arb_element_mod_q(), arb_element_mod_q(), arb_elgamal_keypair())
    def test_encryption_decryption_inverses2(self, message: ElementModQ, nonce: ElementModQ, keypair: ElGamalKeyPair):
        elem = message_to_element(message.elem)
        ciphertext = encrypt(elem, nonce, keypair.public_key)
        plaintext = decrypt_known_nonce(ciphertext, keypair.public_key, nonce)

        self.assertEqual(elem, plaintext)

    @given(arb_element_mod_q())
    def test_large_values_rejected_by_message_to_element(self, q: ElementModQ):
        oversize = q.elem + Q
        self.assertRaises(Exception, message_to_element, oversize)

    def test_no_mult_inv_of_zero(self):
        self.assertRaises(Exception, mult_inv_p, ZERO_MOD_P)

    @given(arb_element_mod_p_no_zero())
    def test_mult_inverses(self, elem: ElementModP):
        inv = mult_inv_p(elem)
        self.assertEqual(mult_mod_p(elem, inv), ONE_MOD_P)


if __name__ == "__main__":
    unittest.main()
