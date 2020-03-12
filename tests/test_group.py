import unittest
from hypothesis import given, strategies as st
from hypothesis.strategies import composite
from electionguard.group import P, Q, ElementModP, ElementModQ, ElGamalKeyPair, g_pow, message_to_element, encrypt, \
    decrypt, decrypt_known_nonce, mult_inv_p, ONE_MOD_P, mult_mod_p, ZERO_MOD_P, G, ONE_MOD_Q, g_pow_q, ZERO_MOD_Q, R, \
    G_INV


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
def arb_elgamal_keypair(draw, elem=arb_element_mod_q_no_zero().filter(lambda x: x.elem > 1)):
    """
    Generates an arbitrary ElGamal secret/public keypair.
    """
    secret_key = draw(elem)
    return ElGamalKeyPair(secret_key, g_pow(secret_key))


# Simple tests that ElGamal satisfies its various inverse and homomorphic properties
# will also exercise the library in general.

class TestElGamal(unittest.TestCase):
    def test_encryption_decryption_simplistic(self):
        message = ElementModQ(0)
        nonce = ElementModQ(1)
        secret_key = ElementModQ(2)
        public_key = g_pow_q(secret_key)
        self.assertLess(public_key.elem, P)

        keypair = ElGamalKeyPair(secret_key, public_key)
        elem = message_to_element(message.elem)
        self.assertEqual(elem.elem, 1)  # g^0 == 1

        ciphertext = encrypt(elem, nonce, keypair.public_key)
        self.assertEqual(G, ciphertext.alpha.elem)
        self.assertEqual(pow(ciphertext.alpha.elem, secret_key.elem, P), pow(public_key.elem, nonce.elem, P))
        self.assertEqual(ciphertext.beta.elem, pow(public_key.elem, nonce.elem, P))

        plaintext = decrypt(ciphertext, keypair.secret_key)

        self.assertEqual(elem, plaintext)

    @given(arb_element_mod_q(), arb_element_mod_q_no_zero(), arb_elgamal_keypair())
    def test_encryption_decryption_inverses(self, message: ElementModQ, nonce: ElementModQ, keypair: ElGamalKeyPair):
        elem = message_to_element(message.elem)
        ciphertext = encrypt(elem, nonce, keypair.public_key)
        plaintext = decrypt(ciphertext, keypair.secret_key)

        self.assertEqual(elem, plaintext)

    @given(arb_element_mod_q(), arb_element_mod_q_no_zero(), arb_elgamal_keypair())
    def test_encryption_decryption_inverses2(self, message: ElementModQ, nonce: ElementModQ, keypair: ElGamalKeyPair):
        elem = message_to_element(message.elem)
        ciphertext = encrypt(elem, nonce, keypair.public_key)
        plaintext = decrypt_known_nonce(ciphertext, keypair.public_key, nonce)

        self.assertEqual(elem, plaintext)

    @given(arb_element_mod_q())
    def test_large_values_rejected_by_message_to_element(self, q: ElementModQ):
        oversize = q.elem + Q
        self.assertRaises(Exception, message_to_element, oversize)

    @given(arb_elgamal_keypair())
    def test_elgamal_keypairs_are_sane(self, keypair: ElGamalKeyPair):
        self.assertLess(keypair.public_key.elem, P)
        self.assertLess(keypair.secret_key.elem, G)
        self.assertEqual(g_pow_q(keypair.secret_key), keypair.public_key)

    def test_no_mult_inv_of_zero(self):
        self.assertRaises(Exception, mult_inv_p, ZERO_MOD_P)

    @given(arb_element_mod_p_no_zero())
    def test_mult_inverses(self, elem: ElementModP):
        inv = mult_inv_p(elem)
        self.assertEqual(mult_mod_p(elem, inv), ONE_MOD_P)

    def test_properties_for_constants(self):
        self.assertNotEqual(G, 1)
        self.assertEqual((R * Q) % P, P - 1)
        self.assertLess(Q, P)
        self.assertLess(G, P)
        self.assertLess(G_INV, P)
        self.assertLess(R, P)

    def test_simple_powers(self):
        gp = ElementModP(G)
        self.assertEqual(gp, g_pow_q(ONE_MOD_Q))
        self.assertEqual(ONE_MOD_P, g_pow_q(ZERO_MOD_Q))


if __name__ == "__main__":
    unittest.main()
