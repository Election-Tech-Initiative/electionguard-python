# Support for basic modular math in ElectionGuard. This code's primary purpose is to be "correct",
# in the sense that performance may be less than hand-optimized C code, and no guarantees are
# made about timing or other side-channels.

from typing import NamedTuple
from typing import Final

# Constants used by ElectionGuard
Q: Final[int] = pow(2, 256) - 189
P: Final[int] = pow(2, 4096) - 69 * Q - 2650872664557734482243044168410288960
R: Final[int] = ((P - 1) * pow(Q, -1, P)) % P
G: Final[int] = pow(2, R, P)
G_INV: Final[int] = pow(G, -1, P)


class ElementModQ(NamedTuple):
    """An element of the smaller `mod q` space, i.e., in [0, Q), where Q is a 256-bit prime."""
    elem: int


ZERO_MOD_Q: Final[ElementModQ] = ElementModQ(0)
ONE_MOD_Q: Final[ElementModQ] = ElementModQ(1)


class ElementModP(NamedTuple):
    """An element of the larger `mod p` space, i.e., in [0, P), where P is a 4096-bit prime."""
    elem: int


ZERO_MOD_P: Final[ElementModP] = ElementModP(0)
ONE_MOD_P: Final[ElementModP] = ElementModP(1)


class ElGamalKeyPair(NamedTuple):
    """A tuple of an ElGamal secret key and public key."""
    secret_key: ElementModQ
    public_key: ElementModP


class ElGamalCiphertext(NamedTuple):
    """An ElGamal ciphertext."""
    alpha: ElementModP
    beta: ElementModP


def message_to_element(m: int) -> ElementModP:
    """
    Encoding a message (expected to be non-negative and less than Q) suitable for ElGamal encryption
    and homomorphic addition (in the exponent).
    """
    if m < 0 or m >= Q:
        raise Exception("Message %d out of range" % m)
    return ElementModP(pow(G, m, P))


def mult_inv_p(e: ElementModP) -> ElementModP:
    """
    Computes the multiplicative inverse mod p.
    :param e:  An element in [1, P).
    """
    if e.elem == 0:
        raise Exception("No multiplicative inverse for zero")
    return ElementModP(pow(e.elem, -1, P))


def pow_mod_p(b: ElementModP, e: ElementModP) -> ElementModP:
    """
    Computes b^e mod p.
    :param b: An element in [0,P).
    :param e: An element in [0,P).
    :return:
    """
    return ElementModP(pow(b.elem, e.elem, P))


def pow_q_mod_p(b: ElementModP, q: ElementModQ) -> ElementModP:
    """
    Computes b^q mod p.
    :param b: An element in [0,P).
    :param q: An element in [0,Q).
    """
    return ElementModP(pow(b.elem, q.elem, P))


def mult_mod_p(a: ElementModP, b: ElementModP) -> ElementModP:
    """
    Computes a* b mod p.
    :param a: An element in [0,P).
    :param b: An element in [0,P).
    """
    return ElementModP((a.elem * b.elem) % P)


def g_pow_q(q: ElementModQ) -> ElementModP:
    """
    Computes g^q mod p.
    :param q: An element in [0,Q).
    """
    return pow_q_mod_p(ElementModP(G), q)


def g_pow(e: ElementModP) -> ElementModP:
    """
    Computes g^e mod p.
    :param e: An element in [0,P).
    """
    return pow_mod_p(ElementModP(G), e)


def encrypt(m: ElementModP, nonce: ElementModQ, public_key: ElementModP) -> ElGamalCiphertext:
    """
    Encrypts a message with a given random nonce and an ElGamal public key.
    :param m: Message to encrypt (e.g., the output of `message_to_element`).
    :param nonce: Randomly chosen nonce in [0,Q).
    :param public_key: ElGamal public key.
    :return: A ciphertext tuple.
    """
    return ElGamalCiphertext(g_pow_q(nonce), mult_mod_p(m, pow_q_mod_p(public_key, nonce)))


def decrypt_known_product(c: ElGamalCiphertext, product: ElementModP) -> ElementModP:
    """
    Decrypts an ElGamal ciphertext with a "known product" (the blinding factor used in the encryption).
    :param c: The ciphertext tuple.
    :param product: The known product (blinding factor).
    :return: An exponentially encoded plaintext message.
    """
    return mult_mod_p(c.beta, mult_inv_p(product))


def decrypt(c: ElGamalCiphertext, secret_key: ElementModQ) -> ElementModP:
    """
    Decrypt an ElGamal ciphertext using a known ElGamal secret key.
    :param c: The ciphertext tuple.
    :param secret_key: The corresponding ElGamal secret key.
    :return: An exponentially encoded plaintext message.
    """
    return decrypt_known_product(c, pow_q_mod_p(c.alpha, secret_key))


def decrypt_known_nonce(c: ElGamalCiphertext, public_key: ElementModP, nonce: ElementModQ) -> ElementModP:
    """
    Decrypt an ElGamal ciphertext using a known nonce and the ElGamal public key.
    :param c: The ciphertext tuple.
    :param public_key: The corresponding ElGamal public key.
    :param nonce: The secret nonce used to create the ciphertext.
    :return: An exponentially encoded plaintext message.
    """
    return decrypt_known_product(c, pow_q_mod_p(public_key, nonce))
