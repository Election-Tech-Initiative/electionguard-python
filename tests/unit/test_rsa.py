from tests.base_test_case import BaseTestCase

from electionguard.rsa import rsa_decrypt, rsa_encrypt, rsa_keypair


class TestRSA(BaseTestCase):
    """RSA encryption tests"""

    def test_rsa_encrypt(self) -> None:
        # Arrange
        message = (
            "9893e1c926521dc595d501056d03c4387b87986089539349"
            "bed6eb1018229b2e0029dd38647bfc80746726b3710c8ac3f"
            "69187da2234b438370a4348a784791813b9857446eb14afc67"
            "6eece5b789a207bcf633ba1676d3410913ae46dd247166c6a682cb0ccc5ecde53"
        )
        # Act
        key_pair = rsa_keypair()
        encrypted_message = rsa_encrypt(message, key_pair.public_key)
        decrypted_message = rsa_decrypt(encrypted_message, key_pair.private_key)

        # Assert
        self.assertIsNotNone(key_pair)
        self.assertGreater(len(key_pair.private_key), 0)
        self.assertGreater(len(key_pair.public_key), 0)

        self.assertIsNotNone(encrypted_message)
        self.assertIsNotNone(decrypted_message)

        self.assertEqual(message, decrypted_message)
