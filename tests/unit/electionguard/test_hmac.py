from electionguard.hmac import get_hmac

from tests.base_test_case import BaseTestCase


class TestHmac(BaseTestCase):
    """HMAC tests"""

    def test_get_hmac(self) -> None:
        """
        Validate that hmac can be generated correctly.
        """

        # Arrange
        key = b"mock_key"
        message = b"mock_message"
        length = 256
        start = 1

        # Act
        hmac_1 = get_hmac(key, message)
        hmac_2 = get_hmac(key, message, length)
        hmac_3 = get_hmac(key, message, length, start)

        # Assert
        self.assertIsNotNone(hmac_1)
        self.assertIsNotNone(hmac_2)
        self.assertIsNotNone(hmac_3)
