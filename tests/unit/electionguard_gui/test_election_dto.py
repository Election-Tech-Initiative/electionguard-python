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

    def test_sum_two_ballots(self) -> None:
        # ARRANGE
        election_dto = ElectionDto(
            {
                "ballot_uploads": [
                    {
                        "ballot_count": 1,
                        "ballot_type": "ballot_type_1",
                    },
                    {
                        "ballot_count": 2,
                        "ballot_type": "ballot_type_2",
                    },
                ]
            }
        )

        # ACT
        result = election_dto.sum_ballots()

        # ASSERT
        self.assertEqual(3, result)

    def test_sum_zero_ballots(self) -> None:
        # ARRANGE
        election_dto = ElectionDto({"ballot_uploads": []})

        # ACT
        result = election_dto.sum_ballots()

        # ASSERT
        self.assertEqual(0, result)
