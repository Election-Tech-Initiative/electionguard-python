from typing import NamedTuple

from .dlog import discrete_log
from .group import ElementModQ, ElementModP, Q, G, P, g_pow_p, mult_p, mult_inv_p, pow_p, ZERO_MOD_Q, int_to_p


class ElGamalKeyPair(NamedTuple):
    """A tuple of an ElGamal secret key and public key."""
    secret_key: ElementModQ
    public_key: ElementModP


class ElGamalCiphertext(NamedTuple):
    """An ElGamal ciphertext."""
    alpha: ElementModP
    beta: ElementModP


def _message_to_element(m: int) -> ElementModP:
    """
    Encoding a message (expected to be non-negative, less than Q, and generally much smaller than that)
    suitable for ElGamal encryption and homomorphic addition (in the exponent).
    """
    if m < 0 or m >= Q:
        raise Exception("Message %d out of range" % m)
    return int_to_p(pow(G, m, P))


def encrypt(m: int, nonce: ElementModQ, public_key: ElementModP) -> ElGamalCiphertext:
    """
    Encrypts a message with a given random nonce and an ElGamal public key.
    :param m: Message to encrypt; must be an integer in [0,Q).
    :param nonce: Randomly chosen nonce in [1,Q).
    :param public_key: ElGamal public key.
    :return: A ciphertext tuple.
    """
    if nonce == ZERO_MOD_Q:
        raise Exception("ElGamal encryption requires a non-zero nonce")

    return ElGamalCiphertext(g_pow_p(nonce), mult_p(_message_to_element(m), pow_p(public_key, nonce)))


def decrypt_known_product(c: ElGamalCiphertext, product: ElementModP) -> int:
    """
    Decrypts an ElGamal ciphertext with a "known product" (the blinding factor used in the encryption).
    :param c: The ciphertext tuple.
    :param product: The known product (blinding factor).
    :return: An exponentially encoded plaintext message.
    """
    return discrete_log(mult_p(c.beta, mult_inv_p(product)))


def decrypt(c: ElGamalCiphertext, secret_key: ElementModQ) -> int:
    """
    Decrypt an ElGamal ciphertext using a known ElGamal secret key.
    :param c: The ciphertext tuple.
    :param secret_key: The corresponding ElGamal secret key.
    :return: An exponentially encoded plaintext message.
    """
    return decrypt_known_product(c, pow_p(c.alpha, secret_key))


def decrypt_known_nonce(c: ElGamalCiphertext, public_key: ElementModP, nonce: ElementModQ) -> int:
    """
    Decrypt an ElGamal ciphertext using a known nonce and the ElGamal public key.
    :param c: The ciphertext tuple.
    :param public_key: The corresponding ElGamal public key.
    :param nonce: The secret nonce used to create the ciphertext.
    :return: An exponentially encoded plaintext message.
    """
    return decrypt_known_product(c, pow_p(public_key, nonce))


def elgamal_add(c1: ElGamalCiphertext, c2: ElGamalCiphertext) -> ElGamalCiphertext:
    """
    Homomorphically accumulates two ElGamal ciphertexts by pairwise multiplication. The exponents
    of vote counters will add.
    """
    return ElGamalCiphertext(mult_p(c1.alpha, c2.alpha), mult_p(c1.beta, c2.beta))
