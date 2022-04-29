from unittest import TestCase

from electionguard.encrypt import ContestData, ContestErrorType
from electionguard.serialize import TruncationError, to_raw


class TestEncrypt(TestCase):
    """Test encryption"""

    def test_contest_data_conversion(self) -> None:
        """Test contest data encoding to padded to bytes then decoding."""

        # Arrange
        error = ContestErrorType.OverVote
        error_data = ["overvote-id-1", "overvote-id-2", "overvote-id-3"]
        write_ins = {
            "writein-id-1": "Teri Dactyl",
            "writein-id-2": "Allie Grater",
            "writein-id-3": "Anna Littlical",
            "writein-id-4": "Polly Wannakrakouer",
        }
        overflow_error_data = ["overflow-id" * 50]

        empty_contest_data = ContestData()
        write_in_contest_data = ContestData(write_ins=write_ins)
        overvote_contest_data = ContestData(error, error_data)
        overvote_and_write_in_contest_data = ContestData(error, error_data, write_ins)
        overflow_contest_data = ContestData(error, overflow_error_data, write_ins)

        # Act & Assert
        self._padding_cycle(empty_contest_data)
        self._padding_cycle(write_in_contest_data)
        self._padding_cycle(overvote_contest_data)
        self._padding_cycle(overvote_and_write_in_contest_data)
        self._padding_cycle(overflow_contest_data)

    def _padding_cycle(self, data: ContestData) -> None:
        """Run full cycle of padding and unpadding."""
        EXPECTED_PADDED_LENGTH = 512

        try:
            padded = data.to_bytes()
            unpadded = ContestData.from_bytes(padded)

            self.assertEqual(EXPECTED_PADDED_LENGTH, len(padded))
            self.assertEqual(data, unpadded)

        except TruncationError:
            # Validate JSON exceeds allowed length
            json = to_raw(data)
            self.assertLess(EXPECTED_PADDED_LENGTH, len(json))
