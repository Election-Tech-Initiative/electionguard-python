from electionguard.tally import PlaintextTallySelection
from electionguard_gui.services.plaintext_ballot_service import _get_contest_details
from tests.base_test_case import BaseTestCase


class TestPlaintextBallotService(BaseTestCase):
    """Test the ElectionDto class"""

    def test_zero_write_ins(self) -> None:
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
        self.assertEqual([], result["selections"])
        self.assertEqual(0, result["nonWriteInTotal"])
        self.assertEqual(None, result["writeInTotal"])
