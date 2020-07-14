from unittest import TestCase

from electionguard.rsa import rsa_decrypt, rsa_encrypt, rsa_keypair


class TestRSA(TestCase):
    def test_rsa_encrypt(self) -> None:
        # Arrange
        message = "1118632206964768372384343373859700232583178373031391293942056347262996938448167273037401292830794700541756937515976417908858473208686448118280677278101719098670646913045584007219899471676906742553167177135624664615778816843133781654175330682468454244343379"

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
