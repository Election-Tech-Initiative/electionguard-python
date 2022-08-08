from datetime import datetime

from pytest_mock import MockFixture
from unittest.mock import patch
from electionguard_gui.models.decryption_dto import DecryptionDto
from tests.base_test_case import BaseTestCase

class TestDecryptionDto(BaseTestCase):
    """Test the DecryptionDto class"""

    def test_get_status_with_no_guardians(self) -> None:
        decryption_dto = DecryptionDto({
            "guardians_joined": [],
            "guardians": 2,
        })
        status = decryption_dto.get_status()
        self.assertEquals(status, "waiting for all guardians to join")

    def test_get_status_with_all_guardians_joined_but_not_completed(self) -> None:
        decryption_dto = DecryptionDto({
            "guardians_joined": ["g1","g2"],
            "guardians": 2,
            "completed_at_utc": None
        })
        status = decryption_dto.get_status()
        self.assertEquals(status, "performing decryption")

    def test_get_status_with_all_guardians_joined_and_completed(self) -> None:
        decryption_dto = DecryptionDto({
            "guardians_joined": ["g1"],
            "guardians": 1,
            "completed_at": datetime.utcnow()
        })
        status = decryption_dto.get_status()
        self.assertEquals(status, "decryption complete")

    @patch("electionguard_gui.services.authorization_service.AuthorizationService")
    def test_admins_can_not_join_key_ceremony(self, auth_service: MockFixture):
        decryption_dto = DecryptionDto({
            "guardians_joined": []
        })
        
        auth_service.configure_mock(**{
            "get_user_id.return_value": "admin1",
            "is_admin.return_value": True
        })
        actual = decryption_dto.set_can_join(auth_service)
        self.assertFalse(actual)