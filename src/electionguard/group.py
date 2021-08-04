"""Basic modular math module.

Support for basic modular math in ElectionGuard. This code's primary purpose is to be "correct",
in the sense that performance may be less than hand-optimized C code, and no guarantees are
made about timing or other side-channels.
"""

from typing import Any, Final, NamedTuple, Optional, Union
from base64 import b16decode
from secrets import randbelow

# pylint: disable=no-name-in-module
from gmpy2 import mpz, powmod, invert, to_binary, from_binary

from .constants import get_large_prime, get_small_prime, get_generator


class ElementModQ(NamedTuple):
    """An element of the smaller `mod q` space, i.e., in [0, Q), where Q is a 256-bit prime."""

    elem: mpz

    def to_bytes(self) -> bytes:
        """
        Convert from the element to the representation of bytes by first going through hex.

        This is preferable to directly accessing `elem`, whose representation might change.
        """
        return b16decode(self.to_hex())

    def to_hex(self) -> str:
        """
        Convert from the element to the hex representation of bytes.

        This is preferable to directly accessing `elem`, whose representation might change.
        """
        h = format(self.elem, "02X")
        if len(h) % 2:
            h = "0" + h
        return h

    def to_int(self) -> int:
        """
        Convert from the element to a regular integer.

        This is preferable to directly accessing `elem`, whose representation might change.
        """
        return self.elem

    def is_in_bounds(self) -> bool:
        """
        Validate that the element is actually within the bounds of [0,Q).

        Returns true if all is good, false if something's wrong.
        """
        return 0 <= self.elem < get_small_prime()

    def is_in_bounds_no_zero(self) -> bool:
        """
        Validate that the element is actually within the bounds of [1,Q).

        Returns true if all is good, false if something's wrong.
        """
        return 0 < self.elem < get_small_prime()

    def __ne__(self, other: Any) -> bool:
        """Overload != (not equal to) operator."""
        return (isinstance(other, (ElementModP, ElementModQ))) and not eq_elems(
            self, other
        )

    def __eq__(self, other: Any) -> bool:
        """Overload == (equal to) operator."""
        return (isinstance(other, (ElementModP, ElementModQ))) and eq_elems(self, other)

    def __str__(self) -> str:
        """Overload to string operator."""
        return self.elem.digits()


class ElementModP(NamedTuple):
    """An element of the larger `mod p` space, i.e., in [0, P), where P is a 4096-bit prime."""

    elem: mpz

    def to_hex(self) -> str:
        """
        Converts from the element to the hex representation of bytes.

        This is preferable to directly accessing `elem`, whose representation might change.
        """
        h = format(self.elem, "02X")
        if len(h) % 2:
            h = "0" + h
        return h

    def to_int(self) -> int:
        """
        Convert from the element to a regular integer.

        This is preferable to directly accessing `elem`, whose representation might change.
        """
        return self.elem

    def is_in_bounds(self) -> bool:
        """
        Validate that the element is actually within the bounds of [0,P).

        Returns true if all is good, false if something's wrong.
        """
        return 0 <= self.elem < get_large_prime()

    def is_in_bounds_no_zero(self) -> bool:
        """
        Validate that the element is actually within the bounds of [1,P).

        Returns true if all is good, false if something's wrong.
        """
        return 0 < self.elem < get_large_prime()

    def is_valid_residue(self) -> bool:
        """
        Validate that this element is in Z^r_p.

        Returns true if all is good, false if something's wrong.
        """
        residue = pow_p(self, ElementModQ(mpz(get_small_prime()))) == ONE_MOD_P
        return self.is_in_bounds() and residue

    def __ne__(self, other: Any) -> bool:
        """Overload != (not equal to) operator."""
        return (isinstance(other, (ElementModP, ElementModQ))) and not eq_elems(
            self, other
        )

    def __eq__(self, other: Any) -> bool:
        """Overload == (equal to) operator."""
        return (isinstance(other, (ElementModP, ElementModQ))) and eq_elems(self, other)

    def __str__(self) -> str:
        """Overload to string operator."""
        return self.elem.digits()


# Common constants
ZERO_MOD_Q: Final[ElementModQ] = ElementModQ(mpz(0))
ONE_MOD_Q: Final[ElementModQ] = ElementModQ(mpz(1))
TWO_MOD_Q: Final[ElementModQ] = ElementModQ(mpz(2))

ZERO_MOD_P: Final[ElementModP] = ElementModP(mpz(0))
ONE_MOD_P: Final[ElementModP] = ElementModP(mpz(1))
TWO_MOD_P: Final[ElementModP] = ElementModP(mpz(2))

ElementModPOrQ = Union[ElementModP, ElementModQ]
ElementModPOrQorInt = Union[ElementModP, ElementModQ, int]
ElementModQorInt = Union[ElementModQ, int]
ElementModPorInt = Union[ElementModP, int]


def hex_to_q(input: str) -> Optional[ElementModQ]:
    """
    Given a hex string representing bytes, returns an ElementModQ.

    Returns `None` if the number is out of the allowed [0,Q) range.
    """
    i = int(input, 16)
    if 0 <= i < get_small_prime():
        return ElementModQ(mpz(i))
    return None


def int_to_q(input: Union[str, int]) -> Optional[ElementModQ]:
    """
    Given a Python integer, returns an ElementModQ.

    Returns `None` if the number is out of the allowed [0,Q) range.
    """
    i = int(input)
    if 0 <= i < get_small_prime():
        return ElementModQ(mpz(i))
    return None


def hex_to_q_unchecked(input: str) -> ElementModQ:
    """
    Given a hex string representing bytes, returns an ElementModQ.

    Allows for the input to be out-of-bounds, and thus creating an invalid
    element (i.e., outside of [0,Q)). Useful for tests or if
    you're absolutely, positively, certain the input is in-bounds.
    """
    i = int(input, 16)
    return ElementModQ(mpz(i))


def int_to_q_unchecked(i: Union[str, int]) -> ElementModQ:
    """
    Given a Python integer, returns an ElementModQ.

    Allows for the input to be out-of-bounds, and thus creating an invalid
    element (i.e., outside of [0,Q)). Useful for tests or if
    you're absolutely, positively, certain the input is in-bounds.
    """
    m = mpz(int(i))
    return ElementModQ(m)


def hex_to_p(input: str) -> Optional[ElementModP]:
    """
    Given a hex string representing bytes, returns an ElementModP.

    Returns `None` if the number is out of the allowed [0,Q) range.
    """
    i = int(input, 16)
    if 0 <= i < get_large_prime():
        return ElementModP(mpz(i))
    return None


def int_to_p(input: Union[str, int]) -> Optional[ElementModP]:
    """
    Given a Python integer, returns an ElementModP.

    Returns `None` if the number is out of the allowed [0,P) range.
    """
    i = int(input)
    if 0 <= i < get_large_prime():
        return ElementModP(mpz(i))
    return None


def hex_to_p_unchecked(input: str) -> ElementModP:
    """
    Given a hex string representing bytes, returns an ElementModP.

    Allows for the input to be out-of-bounds, and thus creating an invalid
    element (i.e., outside of [0,P)). Useful for tests or if
    you're absolutely, positively, certain the input is in-bounds.
    """
    i = int(input, 16)
    return ElementModP(mpz(i))


def int_to_p_unchecked(i: Union[str, int]) -> ElementModP:
    """
    Given a Python integer, returns an ElementModP.

    Allows for the input to be out-of-bounds, and thus creating an invalid
    element (i.e., outside of [0,P)). Useful for tests or if
    you're absolutely, positively, certain the input is in-bounds.
    """
    m = mpz(int(i))
    return ElementModP(m)


def q_to_bytes(e: ElementModQ) -> bytes:
    """Return a byte sequence from the element."""
    return to_binary(e.elem)


def bytes_to_q(b: bytes) -> ElementModQ:
    """Return an element from a byte sequence."""
    return ElementModQ(mpz(from_binary(b)))


def add_q(*elems: ElementModQorInt) -> ElementModQ:
    """Add together one or more elements in Q, returns the sum mod Q."""
    t = mpz(0)
    for e in elems:
        if isinstance(e, int):
            e = int_to_q_unchecked(e)
        t = (t + e.elem) % get_small_prime()

    return ElementModQ(t)


def a_minus_b_q(a: ElementModQorInt, b: ElementModQorInt) -> ElementModQ:
    """Compute (a-b) mod q."""
    if isinstance(a, int):
        a = int_to_q_unchecked(a)
    if isinstance(b, int):
        b = int_to_q_unchecked(b)

    return ElementModQ((a.elem - b.elem) % get_small_prime())


def div_p(a: ElementModPOrQorInt, b: ElementModPOrQorInt) -> ElementModP:
    """Compute a/b mod p."""
    if isinstance(a, int):
        a = int_to_p_unchecked(a)
    if isinstance(b, int):
        b = int_to_p_unchecked(b)

    inverse = invert(b.elem, mpz(get_large_prime()))
    return mult_p(a, int_to_p_unchecked(inverse))


def div_q(a: ElementModPOrQorInt, b: ElementModPOrQorInt) -> ElementModQ:
    """Compute a/b mod q."""
    if isinstance(a, int):
        a = int_to_p_unchecked(a)
    if isinstance(b, int):
        b = int_to_p_unchecked(b)

    inverse = invert(b.elem, mpz(get_small_prime()))
    return mult_q(a, int_to_q_unchecked(inverse))


def negate_q(a: ElementModQorInt) -> ElementModQ:
    """Compute (Q - a) mod q."""
    if isinstance(a, int):
        a = int_to_q_unchecked(a)
    return ElementModQ(get_small_prime() - a.elem)


def a_plus_bc_q(
    a: ElementModQorInt, b: ElementModQorInt, c: ElementModQorInt
) -> ElementModQ:
    """Compute (a + b * c) mod q."""
    if isinstance(a, int):
        a = int_to_q_unchecked(a)
    if isinstance(b, int):
        b = int_to_q_unchecked(b)
    if isinstance(c, int):
        c = int_to_q_unchecked(c)

    return ElementModQ((a.elem + b.elem * c.elem) % get_small_prime())


def mult_inv_p(e: ElementModPOrQorInt) -> ElementModP:
    """
    Compute the multiplicative inverse mod p.

    :param e:  An element in [1, P).
    """
    if isinstance(e, int):
        e = int_to_p_unchecked(e)

    assert e.elem != 0, "No multiplicative inverse for zero"
    return ElementModP(powmod(e.elem, -1, get_large_prime()))


def pow_p(b: ElementModPOrQorInt, e: ElementModPOrQorInt) -> ElementModP:
    """
    Compute b^e mod p.

    :param b: An element in [0,P).
    :param e: An element in [0,P).
    """

    if isinstance(b, int):
        b = int_to_p_unchecked(b)
    if isinstance(e, int):
        e = int_to_p_unchecked(e)

    return ElementModP(powmod(b.elem, e.elem, get_large_prime()))


def pow_q(b: ElementModQorInt, e: ElementModQorInt) -> ElementModQ:
    """
    Compute b^e mod q.

    :param b: An element in [0,Q).
    :param e: An element in [0,Q).
    """
    if isinstance(b, int):
        b = int_to_q_unchecked(b)

    if isinstance(e, int):
        e = int_to_q_unchecked(e)

    return ElementModQ(powmod(b.elem, e.elem, get_small_prime()))


def mult_p(*elems: ElementModPOrQorInt) -> ElementModP:
    """
    Compute the product, mod p, of all elements.

    :param elems: Zero or more elements in [0,P).
    """
    product = mpz(1)
    for x in elems:
        if isinstance(x, int):
            x = int_to_p_unchecked(x)
        product = (product * x.elem) % get_large_prime()
    return ElementModP(product)


def mult_q(*elems: ElementModPOrQorInt) -> ElementModQ:
    """
    Compute the product, mod q, of all elements.

    :param elems: Zero or more elements in [0,Q).
    """
    product = mpz(1)
    for x in elems:
        if isinstance(x, int):
            x = int_to_p_unchecked(x)
        product = (product * x.elem) % get_small_prime()
    return ElementModQ(product)


def g_pow_p(e: ElementModPOrQ) -> ElementModP:
    """
    Compute g^e mod p.

    :param e: An element in [0,P).
    """
    return pow_p(ElementModP(mpz(get_generator())), e)


def rand_q() -> ElementModQ:
    """
    Generate random number between 0 and Q.

    :return: Random value between 0 and Q
    """
    return int_to_q_unchecked(randbelow(get_small_prime()))


def rand_range_q(start: ElementModQorInt) -> ElementModQ:
    """
    Generate random number between start and Q.

    :param start: Starting value of range
    :return: Random value between start and Q
    """
    if isinstance(start, ElementModQ):
        start = start.to_int()

    random = 0
    while random < start:
        random = randbelow(get_small_prime())
    return int_to_q_unchecked(random)


def eq_elems(a: ElementModPOrQ, b: ElementModPOrQ) -> bool:
    """Return whether the two elements hold the same value."""
    return a.elem == b.elem
