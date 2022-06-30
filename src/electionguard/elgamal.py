from dataclasses import dataclass
from typing import Any, Iterable, Optional, Union


from .big_integer import bytes_to_hex
from .byte_padding import to_padded_bytes
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
from .hmac import get_hmac
from .logs import log_info, log_error
from .utils import get_optional

ElGamalSecretKey = ElementModQ
ElGamalPublicKey = ElementModP

_BLOCK_SIZE = 32


@dataclass
class ElGamalKeyPair:
    """A tuple of an ElGamal secret key and public key."""

    secret_key: ElGamalSecretKey
    public_key: ElGamalPublicKey


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

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ElGamalCiphertext):
            return self.pad == other.pad and self.data == other.data
        return False

    def decrypt_known_product(self, product: ElementModP) -> int:
        """
        Decrypts an ElGamal ciphertext with a "known product" (the blinding factor used in the encryption).

        :param product: The known product (blinding factor).
        :return: An exponentially encoded plaintext message.
        """
        return DiscreteLog().discrete_log(mult_p(self.data, mult_inv_p(product)))

    def decrypt(self, secret_key: ElGamalSecretKey) -> int:
        """
        Decrypt an ElGamal ciphertext using a known ElGamal secret key.

        :param secret_key: The corresponding ElGamal secret key.
        :return: An exponentially encoded plaintext message.
        """
        return self.decrypt_known_product(pow_p(self.pad, secret_key))

    def decrypt_known_nonce(
        self, public_key: ElGamalPublicKey, nonce: ElementModQ
    ) -> int:
        """
        Decrypt an ElGamal ciphertext using a known nonce and the ElGamal public key.

        :param public_key: The corresponding ElGamal public key.
        :param nonce: The secret nonce used to create the ciphertext.
        :return: An exponentially encoded plaintext message.
        """
        return self.decrypt_known_product(pow_p(public_key, nonce))

    def partial_decrypt(self, secret_key: ElGamalSecretKey) -> ElementModP:
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


@dataclass
class HashedElGamalCiphertext:
    """
    A hashed version of ElGamal Ciphertext with less size restrictions.
    Create one with `hashed_elgamal_encrypt`. Add them with `elgamal_add`.
    Decrypt using one of the supplied instance methods.
    """

    pad: ElementModP
    """pad or alpha"""

    data: str
    """encrypted data or beta"""

    mac: str
    """message authentication code for hmac"""

    def decrypt(
        self, secret_key: ElGamalSecretKey, encryption_seed: ElementModQ
    ) -> Union[bytes, None]:
        """
        Decrypt an ElGamal ciphertext using a known ElGamal secret key.

        :param secret_key: The corresponding ElGamal secret key.
        :param encryption_seed: Encryption seed (Q) for election.
        :return: Decrypted plaintext message.
        """

        session_key = hash_elems(self.pad, pow_p(self.pad, secret_key))
        data_bytes = to_padded_bytes(self.data)

        (ciphertext_chunks, bit_length) = _get_chunks(data_bytes)
        mac_key = get_hmac(
            session_key.to_hex_bytes(),
            encryption_seed.to_hex_bytes(),
            bit_length,
        )
        to_mac = self.pad.to_hex_bytes() + data_bytes
        mac = bytes_to_hex(get_hmac(mac_key, to_mac))

        if mac != self.mac:
            log_error("MAC verification failed in decryption.")
            return None

        data = b""
        for i, block in enumerate(ciphertext_chunks):
            data_key = get_hmac(
                session_key.to_hex_bytes(),
                encryption_seed.to_hex_bytes(),
                bit_length,
                (i + 1),
            )
            data += bytes([a ^ b for (a, b) in zip(block, data_key)])
        return data


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


def elgamal_combine_public_keys(keys: Iterable[ElGamalPublicKey]) -> ElGamalPublicKey:
    """
    Combine multiple elgamal public keys into a joint key

    :param keys: list of public elgamal keys
    :return: joint key of elgamal keys
    """
    return mult_p(*keys)


def elgamal_encrypt(
    message: int, nonce: ElementModQ, public_key: ElGamalPublicKey
) -> Optional[ElGamalCiphertext]:
    """
    Encrypts a set length message with a given random nonce and an ElGamal public key.

    :param message: Known length message (m) to elgamal_encrypt; must be an integer in [0,Q).
    :param nonce: Randomly chosen nonce in [1,Q).
    :param public_key: ElGamal public key.
    :return: An `ElGamalCiphertext`.
    """
    if nonce == ZERO_MOD_Q:
        log_error("ElGamal encryption requires a non-zero nonce")
        return None

    pad = g_pow_p(nonce)
    gpowp_m = g_pow_p(message)
    pubkey_pow_n = pow_p(public_key, nonce)
    data = mult_p(gpowp_m, pubkey_pow_n)

    log_info(f": publicKey: {public_key.to_hex()}")
    log_info(f": pad: {pad.to_hex()}")
    log_info(f": data: {data.to_hex()}")

    return ElGamalCiphertext(pad, data)


def hashed_elgamal_encrypt(
    message: bytes,
    nonce: ElementModQ,
    public_key: ElGamalPublicKey,
    encryption_seed: ElementModQ,
) -> HashedElGamalCiphertext:
    """
    Encrypts a variable length byte message with a given random nonce and an ElGamal public key.

    :param message: message (m) to encrypt; must be in bytes.
    :param nonce: Randomly chosen nonce in [1, Q).
    :param public_key: ElGamal public key.
    :param encryption_seed: Encryption seed (Q) for election.
    """

    pad = g_pow_p(nonce)
    pubkey_pow_n = pow_p(public_key, nonce)

    session_key = hash_elems(pad, pubkey_pow_n)

    (message_chunks, bit_length) = _get_chunks(message)
    data = b""
    for i, block in enumerate(message_chunks):
        data_key = get_hmac(
            session_key.to_hex_bytes(),
            encryption_seed.to_hex_bytes(),
            bit_length,
            (i + 1),
        )
        data += bytes([a ^ b for (a, b) in zip(block, data_key)])

    mac_key = get_hmac(
        session_key.to_hex_bytes(), encryption_seed.to_hex_bytes(), bit_length
    )
    to_mac = pad.to_hex_bytes() + data
    mac = get_hmac(mac_key, to_mac)

    log_info(f": publicKey: {public_key.to_hex()}")
    log_info(f": pad: {pad.to_hex()}")
    log_info(f": data: {data!r}")
    log_info(f": mac: {bytes_to_hex(mac)}")
    log_info(f"to_mac {to_mac!r}")

    return HashedElGamalCiphertext(pad, bytes_to_hex(data), bytes_to_hex(mac))


def _get_chunks(message: bytes) -> tuple[list[bytes], int]:
    remainder = len(message) % _BLOCK_SIZE
    if remainder:
        message += bytes([0 for _n in range(_BLOCK_SIZE - remainder)])
    number_of_blocks = int(len(message) / _BLOCK_SIZE)
    return (
        [
            message[_BLOCK_SIZE * i : _BLOCK_SIZE * (i + 1)]
            for i in range(number_of_blocks)
        ],
        len(message) * 8,
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
            mult_p(result.pad, c.pad), mult_p(result.data, c.data)
        )

    return result
