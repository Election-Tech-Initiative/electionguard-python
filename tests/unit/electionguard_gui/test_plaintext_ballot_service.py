from unittest.mock import MagicMock, patch
from electionguard.tally import PlaintextTally, PlaintextTallySelection
from electionguard_gui.services.plaintext_ballot_service import (
    _get_contest_details,
    _get_tally_report,
)
from tests.base_test_case import BaseTestCase


class TestPlaintextBallotService(BaseTestCase):
    """Test the ElectionDto class"""

    def test_get_tally_report_with_no_contests(self) -> None:
        # ARRANGE
        plaintext_ballot = PlaintextTally("tally", {})
        selection_names: dict[str, str] = {}
        selection_write_ins: dict[str, bool] = {}
        parties: dict[str, str] = {}
        contest_names: dict[str, str] = {}

        # ACT
        result = _get_tally_report(
            plaintext_ballot,
            selection_names,
            contest_names,
            selection_write_ins,
            parties,
        )

        # ASSERT
        self.assertEqual(0, len(result))

    @patch("electionguard.tally.PlaintextTallySelection")
    def test_given_one_contest_with_valid_name_when_get_tally_report_then_name_returned(
        self, plaintext_tally_selection: MagicMock
    ) -> None:
        # ARRANGE
        plaintext_tally_selection.object_id = "c-1"
        plaintext_ballot = PlaintextTally("tally", {"c-1": plaintext_tally_selection})
        selection_names: dict[str, str] = {}
        selection_write_ins: dict[str, bool] = {}
        parties: dict[str, str] = {}
        contest_names: dict[str, str] = {"c-1": "Contest 1"}

        # ACT
        result = _get_tally_report(
            plaintext_ballot,
            selection_names,
            contest_names,
            selection_write_ins,
            parties,
        )

        # ASSERT
        self.assertEqual(1, len(result))
        self.assertEqual("Contest 1", result[0]["name"])

    @patch("electionguard.tally.PlaintextTallySelection")
    def test_given_one_contest_with_invalid_name_when_get_tally_report_then_name_is_na(
        self, plaintext_tally_selection: MagicMock
    ) -> None:
        # ARRANGE
        plaintext_tally_selection.object_id = "c-1"
        plaintext_ballot = PlaintextTally("tally", {"c-1": plaintext_tally_selection})
        selection_names: dict[str, str] = {}
        selection_write_ins: dict[str, bool] = {}
        parties: dict[str, str] = {}
        contest_names: dict[str, str] = {}

        # ACT
        result = _get_tally_report(
            plaintext_ballot,
            selection_names,
            contest_names,
            selection_write_ins,
            parties,
        )

        # ASSERT
        self.assertEqual(1, len(result))
        self.assertEqual("n/a", list(result)[0]["name"])

    @patch("electionguard.tally.PlaintextTallySelection")
    @patch("electionguard.tally.PlaintextTallySelection")
    def test_given_two_contests_with_duplicate_names_when_get_tally_report_then_both_names_returned(
        self,
        plaintext_tally_selection1: MagicMock,
        plaintext_tally_selection2: MagicMock,
    ) -> None:
        # ARRANGE
        plaintext_tally_selection1.object_id = "c-1"
        plaintext_tally_selection2.object_id = "c-2"
        plaintext_ballot = PlaintextTally(
            "tally",
            {
                "c-1": plaintext_tally_selection1,
                "c-2": plaintext_tally_selection2,
            },
        )
        selection_names: dict[str, str] = {}
        selection_write_ins: dict[str, bool] = {}
        parties: dict[str, str] = {}
        contest_names: dict[str, str] = {"c-1": "My Contest", "c-2": "My Contest"}

        # ACT
        result = _get_tally_report(
            plaintext_ballot,
            selection_names,
            contest_names,
            selection_write_ins,
            parties,
        )

        # ASSERT
        self.assertEqual(2, len(result))
        self.assertEqual("My Contest", list(result)[0]["name"])
        self.assertEqual("My Contest", list(result)[1]["name"])

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

    @patch("electionguard.tally.PlaintextTallySelection")
    @patch("electionguard.tally.PlaintextTallySelection")
    def test_duplicate_section_names(
        self,
        plaintext_tally_selection1: MagicMock,
        plaintext_tally_selection2: MagicMock,
    ) -> None:
        # ARRANGE
        plaintext_tally_selection1.object_id = "S1"
        plaintext_tally_selection1.tally = 1
        plaintext_tally_selection2.object_id = "S2"
        plaintext_tally_selection2.tally = 9
        selections: list[PlaintextTallySelection] = [
            plaintext_tally_selection1,
            plaintext_tally_selection2,
        ]
        selection_names: dict[str, str] = {
            "S1": "Abraham Lincoln",
            "S2": "Abraham Lincoln",
        }
        selection_write_ins: dict[str, bool] = {
            "S1": False,
            "S2": False,
        }
        parties: dict[str, str] = {
            "S1": "National Union Party",
            "S2": "National Union Party",
        }

        # ACT
        result = _get_contest_details(
            selections, selection_names, selection_write_ins, parties
        )

        # ASSERT
        self.assertEqual(10, result["nonWriteInTotal"])
        self.assertEqual(None, result["writeInTotal"])
        self.assertEqual(2, len(result["selections"]))

        selection = result["selections"][0]
        self.assertEqual("Abraham Lincoln", selection["name"])
        self.assertEqual(1, selection["tally"])
        self.assertEqual("National Union Party", selection["party"])
        self.assertEqual(0.1, selection["percent"])

        selection = result["selections"][1]
        self.assertEqual("Abraham Lincoln", selection["name"])
        self.assertEqual(9, selection["tally"])
        self.assertEqual("National Union Party", selection["party"])
        self.assertEqual(0.9, selection["percent"])

    @patch("electionguard.tally.PlaintextTallySelection")
    def test_one_write_in(self, plaintext_tally_selection: MagicMock) -> None:
        # ARRANGE
        plaintext_tally_selection.object_id = "ST"
        plaintext_tally_selection.tally = 1
        selections: list[PlaintextTallySelection] = [plaintext_tally_selection]
        selection_names: dict[str, str] = {}
        selection_write_ins: dict[str, bool] = {
            "ST": True,
        }
        parties: dict[str, str] = {}

        # ACT
        result = _get_contest_details(
            selections, selection_names, selection_write_ins, parties
        )

        # ASSERT
        self.assertEqual(0, result["nonWriteInTotal"])
        self.assertEqual(1, result["writeInTotal"])
        self.assertEqual(0, len(result["selections"]))

    @patch("electionguard.tally.PlaintextTallySelection")
    def test_zero_write_in(self, plaintext_tally_selection: MagicMock) -> None:
        # ARRANGE
        plaintext_tally_selection.object_id = "ST"
        plaintext_tally_selection.tally = 0
        selections: list[PlaintextTallySelection] = [plaintext_tally_selection]
        selection_names: dict[str, str] = {}
        selection_write_ins: dict[str, bool] = {
            "ST": True,
        }
        parties: dict[str, str] = {}

        # ACT
        result = _get_contest_details(
            selections, selection_names, selection_write_ins, parties
        )

        # ASSERT
        self.assertEqual(0, result["nonWriteInTotal"])
        self.assertEqual(0, result["writeInTotal"])
        self.assertEqual(0, len(result["selections"]))
