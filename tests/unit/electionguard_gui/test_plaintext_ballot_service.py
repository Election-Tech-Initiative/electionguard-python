from unittest.mock import MagicMock, patch
from electionguard.tally import PlaintextTallySelection
from electionguard_gui.services.plaintext_ballot_service import _get_contest_details
from tests.base_test_case import BaseTestCase


class TestPlaintextBallotService(BaseTestCase):
    """Test the ElectionDto class"""

    def test_zero_sections(self) -> None:
        # ARRANGE
        selections: list[PlaintextTallySelection] = []
        selection_names: dict[str, str] = {}
        selection_write_ins: dict[str, bool] = {}
        parties: dict[str, str] = {}

        # ACT
        result = _get_contest_details(
            selections, selection_names, selection_write_ins, parties
        )

        # ASSERT
        self.assertEqual(0, result["nonWriteInTotal"])
        self.assertEqual(None, result["writeInTotal"])
        self.assertEqual(0, len(result["selections"]))

    @patch("electionguard.tally.PlaintextTallySelection")
    def test_one_non_write_in(self, plaintext_tally_selection: MagicMock) -> None:
        # ARRANGE
        plaintext_tally_selection.object_id = "AL"
        plaintext_tally_selection.tally = 2
        selections: list[PlaintextTallySelection] = [plaintext_tally_selection]
        selection_names: dict[str, str] = {
            "AL": "Abraham Lincoln",
        }
        selection_write_ins: dict[str, bool] = {
            "AL": False,
        }
        parties: dict[str, str] = {
            "AL": "National Union Party",
        }

        # ACT
        result = _get_contest_details(
            selections, selection_names, selection_write_ins, parties
        )

        # ASSERT
        self.assertEqual(2, result["nonWriteInTotal"])
        self.assertEqual(None, result["writeInTotal"])
        self.assertEqual(1, len(result["selections"]))
        selection = result["selections"][0]
        self.assertEqual("Abraham Lincoln", selection["name"])
        self.assertEqual(2, selection["tally"])
        self.assertEqual("National Union Party", selection["party"])
        self.assertEqual(1, selection["percent"])
