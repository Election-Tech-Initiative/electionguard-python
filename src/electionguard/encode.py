"""Converting module that define padding and default settings for byte order and byte encoding."""

from enum import IntEnum


BYTE_ORDER = "big"
BYTE_ENCODING = "utf-8"

PAD_INDICATOR_SIZE = 2
_PAD_BYTE = b"\x00"


class PaddedDataSize(IntEnum):
    """Define the sizes for padded data."""

    Bytes_32 = 32 - PAD_INDICATOR_SIZE
    Bytes_64 = 64 - PAD_INDICATOR_SIZE
    Bytes_128 = 128 - PAD_INDICATOR_SIZE
    Bytes_256 = 256 - PAD_INDICATOR_SIZE
    Bytes_512 = 512 - PAD_INDICATOR_SIZE


class TruncationError(ValueError):
    """A specific truncation error to indicate when padded data is truncated."""


def add_padding(
    message: bytes, size: PaddedDataSize, allow_truncation: bool = True
) -> bytes:
    """Add padding to message in bytes."""
    message_length = len(message)
    if message_length > size:
        if allow_truncation:
            message_length = size
        else:
            raise TruncationError(
                "Padded data exceeds allowed padded data size of {size}."
            )
    padding_length = size - message_length
    leading_byte = padding_length.to_bytes(PAD_INDICATOR_SIZE, byteorder=BYTE_ORDER)
    padded = leading_byte + message[:message_length] + _PAD_BYTE * padding_length
    return padded


def remove_padding(padded: bytes, size: PaddedDataSize) -> bytes:
    """Remove padding from padded message in bytes."""

    padding_length = int.from_bytes(padded[:PAD_INDICATOR_SIZE], byteorder=BYTE_ORDER)
    message_end = size + PAD_INDICATOR_SIZE - padding_length
    return padded[PAD_INDICATOR_SIZE:message_end]
