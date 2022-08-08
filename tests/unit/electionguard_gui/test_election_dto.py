from datetime import datetime, timezone

from unittest.mock import MagicMock, patch

import pytest
from pytest_mock import MockerFixture
from electionguard_gui.models.election_dto import ElectionDto
from tests.base_test_case import BaseTestCase

class TestElectionDto(BaseTestCase):
    """Test the ElectionDto class"""

    mocker: MockerFixture

    @pytest.fixture(autouse=True)
    def __inject_fixtures(self, mocker):
        self.mocker = mocker

    def test_get_status_with_no_guardians(self) -> None:
        # ARRANGE
        self.mocker.patch(
            "electionguard_gui.models.election_dto.utc_to_str", 
            return_value="Feb 3, 2022 2:10 PM"
        )
        election_dto = ElectionDto({
            "_id": "ABC",
            "created_at": datetime(2020, 2, 3, 7, 10, 10, 0, tzinfo=timezone.utc),
        })

        # ACT
        result = election_dto.to_dict()

        # ASSERT
        self.assertEquals("ABC", result["id"])
        self.assertEquals(result["created_at"], "Feb 3, 2022 2:10 PM")
