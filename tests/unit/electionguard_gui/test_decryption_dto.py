from datetime import datetime
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
