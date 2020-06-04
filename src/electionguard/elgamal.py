from typing import NamedTuple, Optional

from .dlog import discrete_log
from .group import (
    ElementModQ,
    ElementModP,
    g_pow_p,
    mult_p,
    mult_inv_p,
    ONE_MOD_P,
    pow_p,
    ZERO_MOD_Q,
    int_to_q,
)
from .hash import hash_elems
from .logs import log_error
from .utils import flatmap_optional


class ElGamalKeyPair(NamedTuple):
    """A tuple of an ElGamal secret key and public key."""

    secret_key: ElementModQ
    public_key: ElementModP


class ElGamalCiphertext(NamedTuple):
    """
    An "exponential ElGamal ciphertext" (i.e., with the plaintext in the exponent to allow for
    homomorphic addition). Create one with `elgamal_encrypt`. Add them with `elgamal_add`.
    Decrypt using one of the supplied instance methods.
    """

    alpha: ElementModP
    beta: ElementModP

    def decrypt_known_product(self, product: ElementModP) -> int:
        """
        Decrypts an ElGamal ciphertext with a "known product" (the blinding factor used in the encryption).

        :param product: The known product (blinding factor).
        :return: An exponentially encoded plaintext message.
        """
        return discrete_log(mult_p(self.beta, mult_inv_p(product)))

    def decrypt(self, secret_key: ElementModQ) -> int:
        """
        Decrypt an ElGamal ciphertext using a known ElGamal secret key.

        :param secret_key: The corresponding ElGamal secret key.
        :return: An exponentially encoded plaintext message.
        """
        return self.decrypt_known_product(pow_p(self.alpha, secret_key))

    def decrypt_known_nonce(self, public_key: ElementModP, nonce: ElementModQ) -> int:
        """
        Decrypt an ElGamal ciphertext using a known nonce and the ElGamal public key.

        :param public_key: The corresponding ElGamal public key.
        :param nonce: The secret nonce used to create the ciphertext.
        :return: An exponentially encoded plaintext message.
        """
        return self.decrypt_known_product(pow_p(public_key, nonce))

    def crypto_hash(self) -> ElementModQ:
        """
        Computes a cryptographic hash of this ciphertext.
        """
        return hash_elems(self.alpha, self.beta)


def elgamal_homomorphic_zero() -> ElGamalCiphertext:
    """
    :return: an `ElgamalCiphertext` representing a zero value from which to do homomorphic accumulation
    """
    return ElGamalCiphertext(ONE_MOD_P, ONE_MOD_P)


def elgamal_keypair_from_secret(a: ElementModQ) -> Optional[ElGamalKeyPair]:
    """
    Given an ElGamal secret key (typically, a random number in [2,Q)), returns
    an ElGamal keypair, consisting of the given secret key a and public key g^a.
    """
    secret_key_int = a.to_int()
    if secret_key_int < 2:
        log_error("ElGamal secret key needs to be in [2,Q).")
        return None

    return ElGamalKeyPair(a, g_pow_p(a))


def elgamal_encrypt(
    m: int, nonce: ElementModQ, public_key: ElementModP
) -> Optional[ElGamalCiphertext]:
    """
    Encrypts a message with a given random nonce and an ElGamal public key.

    :param m: Message to elgamal_encrypt; must be an integer in [0,Q).
    :param nonce: Randomly chosen nonce in [1,Q).
    :param public_key: ElGamal public key.
    :return: A ciphertext tuple.
    """
    if nonce == ZERO_MOD_Q:
        log_error("ElGamal encryption requires a non-zero nonce")
        return None

    return flatmap_optional(
        int_to_q(m),
        lambda e: ElGamalCiphertext(
            g_pow_p(nonce), mult_p(g_pow_p(e), pow_p(public_key, nonce))
        ),
    )


def elgamal_add(*ciphertexts: ElGamalCiphertext) -> ElGamalCiphertext:
    """
    Homomorphically accumulates one or more ElGamal ciphertexts by pairwise multiplication. The exponents
    of vote counters will add.
    """
    assert len(ciphertexts) != 0, "Must have one or more ciphertexts for elgamal_add"

    result = ciphertexts[0]
    for c in ciphertexts[1:]:
        result = ElGamalCiphertext(
            mult_p(result.alpha, c.alpha), mult_p(result.beta, c.beta)
        )

    return result
