import unittest
from hypothesis import given, strategies as st
from hypothesis.strategies import composite
from electionguard.group import P, Q, ElementModP, ElementModQ, ElGamalKeyPair, g_pow, message_to_element, encrypt, \
    decrypt, decrypt_known_nonce


@composite
def arb_element_mod_q(draw, elem=st.integers(min_value=0, max_value=Q-1)):
    return ElementModQ(draw(elem))

@composite
def arb_element_mod_q_no_zero(draw, elem=st.integers(min_value=1, max_value=Q-1)):
    return ElementModQ(draw(elem))

@composite
def arb_element_mod_p(draw, elem=st.integers(min_value=0, max_value=P-1)):
    return ElementModP(draw(elem))

@composite
def arb_element_mod_p_no_zero(draw, elem=st.integers(min_value=1, max_value=P-1)):
    return ElementModP(draw(elem))

@composite
def arb_elgamal_keypair(draw, elem=arb_element_mod_q_no_zero()):
    secret_key = draw(elem)
    return ElGamalKeyPair(secret_key, g_pow(secret_key))


# Simple tests that ElGamal satisfies its various inverse and homomorphic properties
# will also exercise the library in general.

class TestElGamal(unittest.TestCase):
    @given(arb_element_mod_q(), arb_element_mod_q(), arb_elgamal_keypair())
    def encryption_decryption_inverses(self, message: ElementModQ, nonce: ElementModQ, keypair: ElGamalKeyPair):
        elem = message_to_element(message.elem)
        ciphertext = encrypt(elem, nonce, keypair.public_key)
        plaintext = decrypt(ciphertext, keypair.secret_key)

        self.assertEquals(elem, plaintext)

    @given(arb_element_mod_q(), arb_element_mod_q(), arb_elgamal_keypair())
    def encryption_decryption_inverses(self, message: ElementModQ, nonce: ElementModQ, keypair: ElGamalKeyPair):
        elem = message_to_element(message.elem)
        ciphertext = encrypt(elem, nonce, keypair.public_key)
        plaintext = decrypt_known_nonce(ciphertext, keypair.public_key, nonce)

        self.assertEquals(elem, plaintext)


if __name__ == "__main__":
    unittest.main()
