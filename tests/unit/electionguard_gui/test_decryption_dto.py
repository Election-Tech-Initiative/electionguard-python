from datetime import datetime

from unittest.mock import MagicMock, patch

from electionguard_gui.models.decryption_dto import DecryptionDto
from tests.base_test_case import BaseTestCase


class TestDecryptionDto(BaseTestCase):
    """Test the DecryptionDto class"""

    def test_no_spoiled_ballots(self) -> None:
        # ARRANGE
        decryption_dto = DecryptionDto({})

        # ACT
        spoiled_ballots = decryption_dto.get_plaintext_spoiled_ballots()

        # ASSERT
        self.assertEqual(0, len(spoiled_ballots))

    def test_get_status_with_no_guardians(self) -> None:
        # ARRANGE
        decryption_dto = DecryptionDto(
            {
                "guardians_joined": [],
                "guardians": 2,
            }
        )

        # ACT
        status = decryption_dto.get_status()

        # ASSERT
        self.assertEqual(status, "waiting for all guardians to join")

    def test_get_status_with_all_guardians_joined_but_not_completed(self) -> None:
        # ARRANGE
        decryption_dto = DecryptionDto(
            {"guardians_joined": ["g1", "g2"], "guardians": 2, "completed_at_utc": None}
        )

        # ACT
        status = decryption_dto.get_status()

        # ASSERT
        self.assertEqual(status, "performing decryption")

    def test_get_status_with_all_guardians_joined_and_completed(self) -> None:
        # ARRANGE
        decryption_dto = DecryptionDto(
            {
                "guardians_joined": ["g1"],
                "guardians": 1,
                "completed_at": datetime.utcnow(),
            }
        )

        # ACT
        status = decryption_dto.get_status()

        # ASSERT
        self.assertEqual(status, "decryption complete")

    @patch("electionguard_gui.services.authorization_service.AuthorizationService")
    def test_admins_can_not_join_key_ceremony(self, auth_service: MagicMock) -> None:
        # ARRANGE
        decryption_dto = DecryptionDto({"guardians_joined": []})

        auth_service.configure_mock(
            **{"get_user_id.return_value": "admin1", "is_admin.return_value": True}
        )

        # ACT
        decryption_dto.set_can_join(auth_service)

        # ASSERT
        self.assertFalse(decryption_dto.can_join)

    @patch("electionguard_gui.services.authorization_service.AuthorizationService")
    def test_users_can_join_key_ceremony_if_not_already_joined(
        self, auth_service: MagicMock
    ) -> None:
        # ARRANGE
        decryption_dto = DecryptionDto({"guardians_joined": []})

        auth_service.configure_mock(
            **{"get_user_id.return_value": "user1", "is_admin.return_value": False}
        )

        # ACT
        decryption_dto.set_can_join(auth_service)

        # ASSERT
        self.assertTrue(decryption_dto.can_join)

    @patch("electionguard_gui.services.authorization_service.AuthorizationService")
    def test_users_cant_join_twice(self, auth_service: MagicMock) -> None:
        # ARRANGE
        decryption_dto = DecryptionDto({"guardians_joined": ["user1"]})

        auth_service.configure_mock(
            **{"get_user_id.return_value": "user1", "is_admin.return_value": False}
        )

        # ACT
        decryption_dto.set_can_join(auth_service)

        # ASSERT
        self.assertFalse(decryption_dto.can_join)
