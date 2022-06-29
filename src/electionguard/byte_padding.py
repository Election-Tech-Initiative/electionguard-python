from enum import IntEnum


_PAD_BYTE = b"\x00"
_BYTE_ORDER = "big"
_PAD_INDICATOR_SIZE = 2


class DataSize(IntEnum):
    """Define the sizes for data."""

    Bytes_512 = 512


class TruncationError(ValueError):
    """A specific truncation error to indicate when padded data is truncated."""


def to_padded_bytes(data: str, size: DataSize = DataSize.Bytes_512) -> bytes:
    """Returns the data field as bytes, padded to the correct size."""

    data_bytes = bytes.fromhex(data)
    if len(data_bytes) >= size:
        return data_bytes
    padding_length = size - len(data_bytes)
    return bytes(padding_length) + data_bytes


def add_padding(
    message: bytes, size: DataSize = DataSize.Bytes_512, allow_truncation: bool = False
) -> bytes:
    """Add padding to message in bytes."""

    message_length = len(message)
    padded_data_size = size - _PAD_INDICATOR_SIZE
    if message_length > padded_data_size:
        if allow_truncation:
            message_length = padded_data_size
        else:
            raise TruncationError(
                "Padded data exceeds allowed padded data size of {padded_data_size}."
            )
    padding_length = padded_data_size - message_length
    leading_byte = padding_length.to_bytes(_PAD_INDICATOR_SIZE, byteorder=_BYTE_ORDER)
    padded = leading_byte + message[:message_length] + _PAD_BYTE * padding_length
    return padded


def remove_padding(padded: bytes, size: DataSize = DataSize.Bytes_512) -> bytes:
    """Remove padding from padded message in bytes."""

    padding_length = int.from_bytes(padded[:_PAD_INDICATOR_SIZE], byteorder=_BYTE_ORDER)
    message_end = size - padding_length
    return padded[_PAD_INDICATOR_SIZE:message_end]
