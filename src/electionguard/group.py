"""Basic modular math module.

Support for basic modular math in ElectionGuard. This code's primary purpose is to be "correct",
in the sense that performance may be less than hand-optimized C code, and no guarantees are
made about timing or other side-channels.
"""

from abc import ABC
from typing import Any, Final, Optional, Union
from base64 import b16decode
from secrets import randbelow
from sys import maxsize

# pylint: disable=no-name-in-module
from gmpy2 import mpz, powmod, invert

from .constants import get_large_prime, get_small_prime, get_generator


class BaseElement(ABC, int):
    """An element limited by mod T within [0, T) where T is determined by an upper_bound function."""

    def __new__(cls, elem: Union[int, str], check_within_bounds: bool = True):  # type: ignore
        """Instantiate ElementModT where elem is an int or its hex representation or mpz."""
        if isinstance(elem, str):
            elem = hex_to_int(elem)
        if check_within_bounds:
            if not 0 <= elem < cls.get_upper_bound():
                raise OverflowError
        return super(BaseElement, cls).__new__(cls, elem)

    def __ne__(self, other: Any) -> bool:
        """Overload != (not equal to) operator."""
        return isinstance(other, (BaseElement, int)) and not int(self) != other

    def __eq__(self, other: Any) -> bool:
        """Overload == (equal to) operator."""
        return isinstance(other, (BaseElement, int)) and int(self) == other

    def __hash__(self) -> int:
        """Overload the hashing function."""
        return hash(self.__int__())

    @classmethod
    def get_upper_bound(cls) -> int:  # pylint: disable=no-self-use
        """Get the upper bound for the element."""
        return maxsize

    def to_hex(self) -> str:
        """
        Convert from the element to the hex representation of bytes.

        This is preferable to directly accessing `elem`, whose representation might change.
        """
        return int_to_hex(self.__int__())

    def to_hex_bytes(self) -> bytes:
        """
        Convert from the element to the representation of bytes by first going through hex.

        This is preferable to directly accessing `elem`, whose representation might change.
        """
        return b16decode(self.to_hex())

    def is_in_bounds(self) -> bool:
        """
        Validate that the element is actually within the bounds of [0,Q).

        Returns true if all is good, false if something's wrong.
        """
        return 0 <= self.__int__() < self.get_upper_bound()

    def is_in_bounds_no_zero(self) -> bool:
        """
        Validate that the element is actually within the bounds of [1,Q).

        Returns true if all is good, false if something's wrong.
        """
        return 1 <= self.__int__() < self.get_upper_bound()


class ElementModQ(BaseElement):
    """An element of the larger `mod p` space, i.e., in [0, P), where P is a 4096-bit prime."""

    @classmethod
    def get_upper_bound(cls) -> int:
        """Get the upper bound for the element."""
        return get_small_prime()


class ElementModP(BaseElement):
    """An element of the larger `mod p` space, i.e., in [0, P), where P is a 4096-bit prime."""

    @classmethod
    def get_upper_bound(cls) -> int:
        """Get the upper bound for the element."""
        return get_large_prime()

    def is_valid_residue(self) -> bool:
        """Validate that this element is in Z^r_p."""
        residue = pow_p(self, get_small_prime()) == ONE_MOD_P
        return self.is_in_bounds() and residue


# Common constants
ZERO_MOD_Q: Final[ElementModQ] = ElementModQ(0)
ONE_MOD_Q: Final[ElementModQ] = ElementModQ(1)
TWO_MOD_Q: Final[ElementModQ] = ElementModQ(2)

ZERO_MOD_P: Final[ElementModP] = ElementModP(0)
ONE_MOD_P: Final[ElementModP] = ElementModP(1)
TWO_MOD_P: Final[ElementModP] = ElementModP(2)

ElementModPOrQ = Union[ElementModP, ElementModQ]
ElementModPOrQorInt = Union[ElementModP, ElementModQ, int]
ElementModQorInt = Union[ElementModQ, int]
ElementModPorInt = Union[ElementModP, int]


def _get_mpz(input: Union[BaseElement, int]) -> mpz:
    """Get BaseElement or integer as mpz."""
    return mpz(input)


def hex_to_int(input: str) -> int:
    """Given a hex string representing bytes, returns an int."""
    return int(input, 16)


def int_to_hex(input: int) -> str:
    """Given an int, returns a hex string representing bytes."""
    hex = format(input, "02X")
    if len(hex) % 2:
        hex = "0" + hex
    return hex


def hex_to_q(input: str) -> Optional[ElementModQ]:
    """
    Given a hex string representing bytes, returns an ElementModQ.

    Returns `None` if the number is out of the allowed [0,Q) range.
    """
    try:
        return ElementModQ(input)
    except OverflowError:
        return None


def int_to_q(input: int) -> Optional[ElementModQ]:
    """
    Given a Python integer, returns an ElementModQ.

    Returns `None` if the number is out of the allowed [0,Q) range.
    """
    try:
        return ElementModQ(input)
    except OverflowError:
        return None


def hex_to_p(input: str) -> Optional[ElementModP]:
    """
    Given a hex string representing bytes, returns an ElementModP.

    Returns `None` if the number is out of the allowed [0,Q) range.
    """
    try:
        return ElementModP(input)
    except OverflowError:
        return None


def int_to_p(input: int) -> Optional[ElementModP]:
    """
    Given a Python integer, returns an ElementModP.

    Returns `None` if the number is out of the allowed [0,P) range.
    """
    try:
        return ElementModP(input)
    except OverflowError:
        return None


def add_q(*elems: ElementModQorInt) -> ElementModQ:
    """Add together one or more elements in Q, returns the sum mod Q."""
    sum = _get_mpz(0)
    for e in elems:
        e = _get_mpz(e)
        sum = (sum + e) % get_small_prime()
    return ElementModQ(sum)


def a_minus_b_q(a: ElementModQorInt, b: ElementModQorInt) -> ElementModQ:
    """Compute (a-b) mod q."""
    a = _get_mpz(a)
    b = _get_mpz(b)
    return ElementModQ((a - b) % get_small_prime())


def div_p(a: ElementModPOrQorInt, b: ElementModPOrQorInt) -> ElementModP:
    """Compute a/b mod p."""
    b = _get_mpz(b)
    inverse = invert(b, _get_mpz(get_large_prime()))
    return mult_p(a, inverse)


def div_q(a: ElementModPOrQorInt, b: ElementModPOrQorInt) -> ElementModQ:
    """Compute a/b mod q."""
    b = _get_mpz(b)
    inverse = invert(b, _get_mpz(get_small_prime()))
    return mult_q(a, inverse)


def negate_q(a: ElementModQorInt) -> ElementModQ:
    """Compute (Q - a) mod q."""
    a = _get_mpz(a)
    return ElementModQ(get_small_prime() - a)


def a_plus_bc_q(
    a: ElementModQorInt, b: ElementModQorInt, c: ElementModQorInt
) -> ElementModQ:
    """Compute (a + b * c) mod q."""
    a = _get_mpz(a)
    b = _get_mpz(b)
    c = _get_mpz(c)
    return ElementModQ((a + b * c) % get_small_prime())


def mult_inv_p(e: ElementModPOrQorInt) -> ElementModP:
    """
    Compute the multiplicative inverse mod p.

    :param e:  An element in [1, P).
    """
    e = _get_mpz(e)
    assert e != 0, "No multiplicative inverse for zero"
    return ElementModP(powmod(e, -1, get_large_prime()))


def pow_p(b: ElementModPOrQorInt, e: ElementModPOrQorInt) -> ElementModP:
    """
    Compute b^e mod p.

    :param b: An element in [0,P).
    :param e: An element in [0,P).
    """
    b = _get_mpz(b)
    e = _get_mpz(e)
    return ElementModP(powmod(b, e, get_large_prime()))


def pow_q(b: ElementModQorInt, e: ElementModQorInt) -> ElementModQ:
    """
    Compute b^e mod q.

    :param b: An element in [0,Q).
    :param e: An element in [0,Q).
    """
    b = _get_mpz(b)
    e = _get_mpz(e)
    return ElementModQ(powmod(b, e, get_small_prime()))


def mult_p(*elems: ElementModPOrQorInt) -> ElementModP:
    """
    Compute the product, mod p, of all elements.

    :param elems: Zero or more elements in [0,P).
    """
    product = _get_mpz(1)
    for x in elems:
        x = _get_mpz(x)
        product = (product * x) % get_large_prime()
    return ElementModP(product)


def mult_q(*elems: ElementModPOrQorInt) -> ElementModQ:
    """
    Compute the product, mod q, of all elements.

    :param elems: Zero or more elements in [0,Q).
    """
    product = _get_mpz(1)
    for x in elems:
        x = _get_mpz(x)
        product = (product * x) % get_small_prime()
    return ElementModQ(product)


def g_pow_p(e: ElementModPOrQorInt) -> ElementModP:
    """
    Compute g^e mod p.

    :param e: An element in [0,P).
    """
    return pow_p(get_generator(), e)


def rand_q() -> ElementModQ:
    """
    Generate random number between 0 and Q.

    :return: Random value between 0 and Q
    """
    return ElementModQ(randbelow(get_small_prime()))


def rand_range_q(start: ElementModQorInt) -> ElementModQ:
    """
    Generate random number between start and Q.

    :param start: Starting value of range
    :return: Random value between start and Q
    """
    start = _get_mpz(start)
    random = 0
    while random < start:
        random = randbelow(get_small_prime())
    return ElementModQ(random)
