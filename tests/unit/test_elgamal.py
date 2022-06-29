from electionguard import ElGamalKeyPair
from electionguard.elgamal import (
    ElGamalPublicKey,
    ElGamalSecretKey,
    hashed_elgamal_encrypt,
)
from electionguard.group import ElementModQ
from electionguard.byte_padding import add_padding, remove_padding
from electionguard.utils import get_optional
from tests.base_test_case import BaseTestCase


class TestElgamal(BaseTestCase):
    """Test decryption methods"""

    def test_hashed_elgamal_with_session_key_that_starts_with_0(self) -> None:
        kp = ElGamalKeyPair(
            secret_key=ElGamalSecretKey("02"),
            public_key=ElGamalPublicKey("A147CA31DE0F48C1"),
        )
        plaintext = b"\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00"

        # these values produce a session_key 2B00, which produces encrypted
        # data that begins with a 0 byte. When hashed_elgamal_encrypt() returns that
        # data it calls bytes_to_hex() which truncates leading zero's. That produces
        # 255 bytes instead of 256 bytes and decrypt() much pad a byte to account for it.
        hmac_nonce = ElementModQ("D8E1")
        hmac_seed = ElementModQ("02F1")

        self.do_hashed_elgamal(kp, plaintext, hmac_nonce, hmac_seed)

    def test_hashed_elgamal_with_session_key_that_starts_with_1(self) -> None:
        kp = ElGamalKeyPair(
            secret_key=ElGamalSecretKey("02"),
            public_key=ElGamalPublicKey("A147CA31DE0F48C1"),
        )
        plaintext = b"\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00"

        # these values produce a session_key EE19 which produces encrypted data that
        # begins with a 1 byte and bytes_to_hex() does not truncate anything
        hmac_nonce = ElementModQ("AB29")
        hmac_seed = ElementModQ("2179")

        self.do_hashed_elgamal(kp, plaintext, hmac_nonce, hmac_seed)

    def do_hashed_elgamal(
        self,
        kp: ElGamalKeyPair,
        plaintext: bytes,
        hmac_nonce: ElementModQ,
        hmac_seed: ElementModQ,
    ) -> None:
        padded_plaintext = add_padding(plaintext)
        hmac = hashed_elgamal_encrypt(
            padded_plaintext, hmac_nonce, kp.public_key, hmac_seed
        )
        decryption_bytes_padded = hmac.decrypt(kp.secret_key, hmac_seed)
        self.assertIsNotNone(decryption_bytes_padded)

        decryption_bytes = remove_padding(get_optional(decryption_bytes_padded))
        self.assertEqual(plaintext, decryption_bytes)
