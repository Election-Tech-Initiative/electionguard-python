from typing import Any, Tuple, Union
from base64 import b16decode

# pylint: disable=no-name-in-module
from gmpy2 import mpz

from .utils import BYTE_ORDER


def _hex_to_int(input: str) -> int:
    """Given a hex string representing bytes, returns an int."""
    valid_bytes = input[1:] if (len(input) % 2 != 0 and input[0] == "0") else input
    hex_bytes = bytes.fromhex(valid_bytes)
    return int.from_bytes(hex_bytes, BYTE_ORDER)


def _int_to_hex(input: int) -> str:
    """Given an int, returns a hex string representing bytes."""

    def pad_hex(hex: str) -> str:
        """Pad hex to ensure 2 digit hexadecimal format maintained."""
        return "0" + hex if len(hex) % 2 else hex

    hex = format(input, "02X")
    return pad_hex(hex)


def bytes_to_hex(input: bytes) -> str:
    return _int_to_hex(int.from_bytes(input, BYTE_ORDER))


_zero = mpz(0)


def _convert_to_element(data: Union[int, str]) -> Tuple[str, int]:
    """Convert element to consistent types"""
    if isinstance(data, str):
        integer = _hex_to_int(data)
        hex = _int_to_hex(integer)
    else:
        hex = _int_to_hex(data)
        integer = data
    return (hex, integer)


class BigInteger(str):
    """A specialized representation of a big integer in python"""

    _value: mpz = _zero

    def __new__(cls, data: Union[int, str]):  # type: ignore
        (hex, integer) = _convert_to_element(data)
        big_int = super(BigInteger, cls).__new__(cls, hex)
        big_int._value = mpz(integer)
        return big_int

    @property
    def value(self) -> mpz:
        """Get internal value for math calculations"""
        return self._value

    def __int__(self) -> int:
        """Overload int conversion."""
        return int(self.value)

    def __eq__(self, other: Any) -> bool:
        """Overload == (equal to) operator."""
        return (
            isinstance(other, BigInteger) and int(self.value) == int(other.value)
        ) or (isinstance(other, int) and int(self.value) == other)

    def __ne__(self, other: Any) -> bool:
        """Overload != (not equal to) operator."""
        return not self == other

    def __lt__(self, other: Any) -> bool:
        """Overload <= (less than) operator."""
        return (
            isinstance(other, BigInteger) and int(self.value) < int(other.value)
        ) or (isinstance(other, int) and int(self.value) < other)

    def __le__(self, other: Any) -> bool:
        """Overload <= (less than or equal) operator."""
        return self.__lt__(other) or self.__eq__(other)

    def __gt__(self, other: Any) -> bool:
        """Overload > (greater than) operator."""
        return (
            isinstance(other, BigInteger) and int(self.value) > int(other.value)
        ) or (isinstance(other, int) and int(self.value) > other)

    def __ge__(self, other: Any) -> bool:
        """Overload >= (greater than or equal) operator."""
        return self.__gt__(other) or self.__eq__(other)

    def __hash__(self) -> int:
        """Overload the hashing function."""
        return hash(self.value)

    def to_hex(self) -> str:
        """
        Convert from the element to the hex representation of bytes.
        """
        return str(self)

    def to_hex_bytes(self) -> bytes:
        """
        Convert from the element to the representation of bytes by first going through hex.
        """

        return b16decode(self)
