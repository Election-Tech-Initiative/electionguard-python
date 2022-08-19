from datetime import datetime, timezone

from electionguard_gui.models.election_dto import ElectionDto
from tests.base_test_case import BaseTestCase


class TestElectionDto(BaseTestCase):
    """Test the ElectionDto class"""

    def test_get_status_with_no_guardians(self) -> None:
        # ARRANGE
        self.mocker.patch(
            "electionguard_gui.models.election_dto.utc_to_str",
            return_value="Feb 3, 2022 2:10 PM",
        )
        election_dto = ElectionDto(
            {
                "_id": "ABC",
                "created_at": datetime(2020, 2, 3, 7, 10, 10, 0, tzinfo=timezone.utc),
            }
        )

        # ACT
        result = election_dto.to_dict()

        # ASSERT
        self.assertEqual("ABC", result["id"])
        self.assertEqual("Feb 3, 2022 2:10 PM", result["created_at"])
