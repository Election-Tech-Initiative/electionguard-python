from unittest import TestCase

from electionguard.encode import (
    BYTE_ENCODING,
    PAD_INDICATOR_SIZE,
    TruncationError,
    add_padding,
    remove_padding,
    PaddedDataSize,
)


class TestEncoding(TestCase):
    """Guardian tests"""

    def test_byte_padding(self) -> None:
        """Test adding and removing padding that will be used."""
        # Arrange
        write_in_data = "write-in-example"
        write_in_size = PaddedDataSize.Bytes_128

        contest_data = "overvote"
        contest_size = PaddedDataSize.Bytes_32

        empty_string = ""
        random_size = PaddedDataSize.Bytes_64

        truncated_string = "A" * 32 + "B"
        truncated_size = PaddedDataSize.Bytes_32

        # Act & Assert
        self.padding_cycle(write_in_data, write_in_size)
        self.padding_cycle(contest_data, contest_size)
        self.padding_cycle(empty_string, random_size)
        self.padding_cycle(truncated_string, truncated_size)

    def padding_cycle(self, input: str, size: PaddedDataSize) -> None:
        """Run full cycle of padding and unpadding."""

        byte_format = bytes(input, BYTE_ENCODING)
        try:
            padded = add_padding(byte_format, size, False)
            unpadded = remove_padding(padded, size)
            output = unpadded.decode(BYTE_ENCODING)

            self.assertEqual(size + PAD_INDICATOR_SIZE, len(padded))
            self.assertEqual(input, output)

        except TruncationError:
            padded = add_padding(byte_format, size, True)
            unpadded = remove_padding(padded, size)
            output = unpadded.decode(BYTE_ENCODING)

            self.assertEqual(size + PAD_INDICATOR_SIZE, len(padded))
            self.assertNotEqual(input, output)
