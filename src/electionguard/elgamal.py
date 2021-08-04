from dataclasses import dataclass
from typing import Iterable, Optional

from .discrete_log import DiscreteLog
from .group import (
    ElementModQ,
    ElementModP,
    g_pow_p,
    mult_p,
    mult_inv_p,
    pow_p,
    ZERO_MOD_Q,
    TWO_MOD_Q,
    rand_range_q,
)
from .hash import hash_elems
from .logs import log_info, log_error
from .utils import get_optional

ELGAMAL_SECRET_KEY = ElementModQ
ELGAMAL_PUBLIC_KEY = ElementModP


@dataclass
class ElGamalKeyPair:
    """A tuple of an ElGamal secret key and public key."""

    secret_key: ELGAMAL_SECRET_KEY
    public_key: ELGAMAL_PUBLIC_KEY


@dataclass
class ElGamalCiphertext:
    """
    An "exponential ElGamal ciphertext" (i.e., with the plaintext in the exponent to allow for
    homomorphic addition). Create one with `elgamal_encrypt`. Add them with `elgamal_add`.
    Decrypt using one of the supplied instance methods.
    """

    pad: ElementModP
    """pad or alpha"""

    data: ElementModP
    """encrypted data or beta"""

    def decrypt_known_product(self, product: ElementModP) -> int:
        """
        Decrypts an ElGamal ciphertext with a "known product" (the blinding factor used in the encryption).

        :param product: The known product (blinding factor).
        :return: An exponentially encoded plaintext message.
        """
        return DiscreteLog().discrete_log(mult_p(self.data, mult_inv_p(product)))

    def decrypt(self, secret_key: ElementModQ) -> int:
        """
        Decrypt an ElGamal ciphertext using a known ElGamal secret key.

        :param secret_key: The corresponding ElGamal secret key.
        :return: An exponentially encoded plaintext message.
        """
        return self.decrypt_known_product(pow_p(self.pad, secret_key))

    def decrypt_known_nonce(self, public_key: ElementModP, nonce: ElementModQ) -> int:
        """
        Decrypt an ElGamal ciphertext using a known nonce and the ElGamal public key.

        :param public_key: The corresponding ElGamal public key.
        :param nonce: The secret nonce used to create the ciphertext.
        :return: An exponentially encoded plaintext message.
        """
        return self.decrypt_known_product(pow_p(public_key, nonce))

    def partial_decrypt(self, secret_key: ElementModQ) -> ElementModP:
        """
        Partially Decrypts an ElGamal ciphertext with a known ElGamal secret key.

        𝑀_i = 𝐴^𝑠𝑖 mod 𝑝 in the spec

        :param secret_key: The corresponding ElGamal secret key.
        :return: An exponentially encoded plaintext message.
        """
        return pow_p(self.pad, secret_key)

    def crypto_hash(self) -> ElementModQ:
        """
        Computes a cryptographic hash of this ciphertext.
        """
        return hash_elems(self.pad, self.data)


def elgamal_keypair_from_secret(a: ElementModQ) -> Optional[ElGamalKeyPair]:
    """
    Given an ElGamal secret key (typically, a random number in [2,Q)), returns
    an ElGamal keypair, consisting of the given secret key a and public key g^a.
    """
    secret_key_int = a
    if secret_key_int < 2:
        log_error("ElGamal secret key needs to be in [2,Q).")
        return None

    return ElGamalKeyPair(a, g_pow_p(a))


def elgamal_keypair_random() -> ElGamalKeyPair:
    """
    Create a random elgamal keypair

    :return: random elgamal key pair
    """
    return get_optional(elgamal_keypair_from_secret(rand_range_q(TWO_MOD_Q)))


def elgamal_combine_public_keys(keys: Iterable[ElementModP]) -> ElementModP:
    """
    Combine multiple elgamal public keys into a joint key

    :param keys: list of public elgamal keys
    :return: joint key of elgamal keys
    """
    return mult_p(*keys)


def elgamal_encrypt(
    m: int, nonce: ElementModQ, public_key: ElementModP
) -> Optional[ElGamalCiphertext]:
    """
    Encrypts a message with a given random nonce and an ElGamal public key.

    :param m: Message to elgamal_encrypt; must be an integer in [0,Q).
    :param nonce: Randomly chosen nonce in [1,Q).
    :param public_key: ElGamal public key.
    :return: An `ElGamalCiphertext`.
    """
    if nonce == ZERO_MOD_Q:
        log_error("ElGamal encryption requires a non-zero nonce")
        return None

    pad = g_pow_p(nonce)
    gpowp_m = g_pow_p(m)
    pubkey_pow_n = pow_p(public_key, nonce)
    data = mult_p(gpowp_m, pubkey_pow_n)

    log_info(f": publicKey: {public_key.to_hex()}")
    log_info(f": pad: {pad.to_hex()}")
    log_info(f": data: {data.to_hex()}")

    return ElGamalCiphertext(pad, data)


def elgamal_add(*ciphertexts: ElGamalCiphertext) -> ElGamalCiphertext:
    """
    Homomorphically accumulates one or more ElGamal ciphertexts by pairwise multiplication. The exponents
    of vote counters will add.
    """
    assert len(ciphertexts) != 0, "Must have one or more ciphertexts for elgamal_add"

    result = ciphertexts[0]
    for c in ciphertexts[1:]:
        result = ElGamalCiphertext(
            mult_p(result.pad, c.pad), mult_p(result.data, c.data)
        )

    return result
