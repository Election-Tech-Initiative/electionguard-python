"""Implementation of Hashing for Message Authentication Codes (HMAC)"""

from hmac import digest
from typing import Optional

_BYTE_LENGTH = 4
_BYTE_ORDER = "little"


def get_hmac(
    key: bytes, message: bytes, length: Optional[int] = None, start: int = 0
) -> bytes:
    """
    Get a hash-based message authentication code(hmac) digest using
    default hashing algorithm.

    :param key: key (k) in bytes
    :param message: message in bytes
    :param length: length (L) of total message
    :param start: starting byte position
    :return: hmac digest in bytes
    """

    if length:
        message = _fix_message_length(message, length, start)

    return digest(key, message, "SHA256")


def _fix_message_length(msg: bytes, length: int, start: int = 0) -> bytes:
    """
    Fix the message length to a set byte length with starting and end bytes.

    :param msg: message
    :param length: length (L)
    :param start: start of byte
    """

    start_byte = start.to_bytes(_BYTE_LENGTH, _BYTE_ORDER)
    end_byte = length.to_bytes(_BYTE_LENGTH, _BYTE_ORDER)
    return start_byte + msg + end_byte
