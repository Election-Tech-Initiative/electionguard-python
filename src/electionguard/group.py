"""Basic modular math module.

Support for basic modular math in ElectionGuard. This code's primary purpose is to be "correct",
in the sense that performance may be less than hand-optimized C code, and no guarantees are
made about timing or other side-channels.
"""

from abc import ABC
from base64 import b16decode
from secrets import randbelow
from typing import Any, Final, Optional, Union

# pylint: disable=no-name-in-module
from gmpy2 import xmpz, powmod, invert

from .constants import (
    get_large_prime,
    get_small_prime,
    get_g_mpz,
    get_p_mpz,
    get_q_mpz,
    get_generator,
    get_g_powradix,
    get_powradix_option,
)
from .powradix import PowRadix


class BaseElement(ABC, int):
    """An element limited by mod T within [0, T) where T is determined by an upper_bound function."""

    def __new__(cls, elem: Union[int, str]):  # type: ignore
        """Instantiate ElementModT where elem is an int or its hex representation or mpz."""

        if isinstance(elem, str):
            elem = hex_to_int(elem)

        return super(BaseElement, cls).__new__(cls, elem)

    def __ne__(self, other: Any) -> bool:
        """Overload != (not equal to) operator."""
        return isinstance(other, (BaseElement, int)) and int(self) != int(other)

    def __eq__(self, other: Any) -> bool:
        """Overload == (equal to) operator."""
        return isinstance(other, (BaseElement, int)) and int(self) == int(other)

    def __hash__(self) -> int:
        """Overload the hashing function."""
        return hash(self.__int__())

    @classmethod
    def get_upper_bound(cls) -> int:  # pylint: disable=no-self-use
        """Get the upper bound for the element."""
        raise RuntimeError(
            "control flow should never get here; should go to one of the subclasses"
        )

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


# Common constants
_negative_one_mpz = xmpz(-1)
_zero_mpz = xmpz(0)
_one_mpz = xmpz(1)


class ElementModQ(BaseElement):
    """An element of the smaller `mod q` space, i.e., in [0, Q), where Q is a 256-bit prime."""

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

    def pow_p(self, exponent: "ElementModPOrQorInt") -> "ElementModP":
        """
        Computes self ^ exponent mod p. Note, these two calls are equivalent::
          x = pow_p(base, exponent)
          x = base.pow_p(exponent)
        """
        b = _get_xmpz(self)
        e = _get_xmpz(exponent)
        return ElementModP(powmod(b, e, get_p_mpz()))

    def accelerate_pow(self) -> "ElementModP":
        """
        Returns a new `ElementModPAcceleratedPow` that's equivalent to this `ElementModP`, but where
        modular exponentiation will go significantly faster. Does not mutate the current object.
        """
        return ElementModPAcceleratedPow(self)


class ElementModPAcceleratedPow(ElementModP):
    """
    An element that's equivalent to a regular `ElementModP`, except that when used as
    the base of a modular exponentiation, internal state will allow this computation
    to run significantly faster.
    """

    pow_radix: PowRadix

    def __new__(cls, elem: Union[int, str]):  # type: ignore
        # We need additional complexity here because the base class of ElementModP has
        # a __new__ and __init__ method. Some discussion of this:
        # https://stackoverflow.com/questions/10788976/how-do-i-properly-inherit-from-a-superclass-that-has-a-new-method
        return ElementModP.__new__(cls, elem)

    def __init__(self, elem: Union[int, str]) -> None:
        # special case for g, since we've already accelerated it
        elem_mpz = _get_xmpz(elem)
        if elem_mpz == get_g_mpz():
            self.pow_radix = get_g_powradix()
        else:
            self.pow_radix = PowRadix(
                _get_xmpz(elem), get_powradix_option(), get_q_mpz(), get_p_mpz()
            )

    def pow_p(self, exponent: "ElementModPOrQorInt") -> ElementModP:
        """
        Computes self ^ exponent mod p, taking advantage of the internal acceleration
        structure. Note, these two calls are equivalent::
          x = pow_p(base, exponent)
          x = base.pow_p(exponent)
        """
        return ElementModP(self.pow_radix.pow(_get_xmpz(exponent)))

    def accelerate_pow(self) -> ElementModP:
        """
        Accelerating something which has already been accelerated is a no-op.
        """
        return self


# Common constants
ZERO_MOD_Q: Final[ElementModQ] = ElementModQ(0)
ONE_MOD_Q: Final[ElementModQ] = ElementModQ(1)
TWO_MOD_Q: Final[ElementModQ] = ElementModQ(2)

ZERO_MOD_P: Final[ElementModP] = ElementModP(0)
ONE_MOD_P: Final[ElementModP] = ElementModP(1)
TWO_MOD_P: Final[ElementModP] = ElementModP(2)

ElementModPOrQ = BaseElement
ElementModPOrQorInt = Union[BaseElement, int]
ElementModQorInt = Union[ElementModQ, int]
ElementModPorInt = Union[ElementModP, int]


def _get_xmpz(input: Union[str, ElementModPOrQorInt]) -> xmpz:
    """Get BaseElement or integer as xmpz."""
    return xmpz(hex_to_int(input) if isinstance(input, str) else input)


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
    result = ElementModQ(input)
    return result if result.is_in_bounds() else None


def int_to_q(input: int) -> Optional[ElementModQ]:
    """
    Given a Python integer, returns an ElementModQ.

    Returns `None` if the number is out of the allowed [0,Q) range.
    """
    result = ElementModQ(input)
    return result if result.is_in_bounds() else None


def hex_to_p(input: str) -> Optional[ElementModP]:
    """
    Given a hex string representing bytes, returns an ElementModP.

    Returns `None` if the number is out of the allowed [0,Q) range.
    """
    result = ElementModP(input)
    return result if result.is_in_bounds() else None


def int_to_p(input: int) -> Optional[ElementModP]:
    """
    Given a Python integer, returns an ElementModP.

    Returns `None` if the number is out of the allowed [0,P) range.
    """
    result = ElementModP(input)
    return result if result.is_in_bounds() else None


def add_q(*elems: ElementModQorInt) -> ElementModQ:
    """Add together one or more elements in Q, returns the sum mod Q."""
    sum = _zero_mpz
    q = get_q_mpz()

    for e in elems:
        e = _get_xmpz(e)
        sum = (sum + e) % q
    return ElementModQ(sum)


def a_minus_b_q(a: ElementModQorInt, b: ElementModQorInt) -> ElementModQ:
    """Compute (a-b) mod q."""
    a = _get_xmpz(a)
    b = _get_xmpz(b)
    tmp = (a - b) % get_q_mpz()
    return ElementModQ(tmp)


def div_p(a: ElementModPOrQorInt, b: ElementModPOrQorInt) -> ElementModP:
    """Compute a/b mod p."""
    b = _get_xmpz(b)
    inverse = invert(b, get_p_mpz())
    return mult_p(a, inverse)


def div_q(a: ElementModPOrQorInt, b: ElementModPOrQorInt) -> ElementModQ:
    """Compute a/b mod q."""
    b = _get_xmpz(b)
    inverse = invert(b, get_q_mpz())
    return mult_q(a, inverse)


def negate_q(a: ElementModQorInt) -> ElementModQ:
    """Compute (Q - a) mod q."""
    a = _get_xmpz(a)
    return ElementModQ(get_q_mpz() - a)


def a_plus_bc_q(
    a: ElementModQorInt, b: ElementModQorInt, c: ElementModQorInt
) -> ElementModQ:
    """Compute (a + b * c) mod q."""
    a = _get_xmpz(a)
    b = _get_xmpz(b)
    c = _get_xmpz(c)
    return ElementModQ((a + b * c) % get_q_mpz())


def mult_inv_p(e: ElementModPOrQorInt) -> ElementModP:
    """
    Compute the multiplicative inverse mod p.

    :param e:  An element in [1, P).
    """
    e = _get_xmpz(e)
    assert e != 0, "No multiplicative inverse for zero"
    tmp = powmod(e, _negative_one_mpz, get_p_mpz())
    return ElementModP(tmp)


def pow_p(b: ElementModPOrQorInt, e: ElementModPOrQorInt) -> ElementModP:
    """
    Compute b^e mod p.

    :param b: An element in [0,P).
    :param e: An element in [0,P).
    """

    if isinstance(b, ElementModP):
        return b.pow_p(e)

    b = _get_xmpz(b)
    e = _get_xmpz(e)
    return ElementModP(powmod(b, e, get_p_mpz()))


def pow_q(b: ElementModQorInt, e: ElementModQorInt) -> ElementModQ:
    """
    Compute b^e mod q.

    :param b: An element in [0,Q).
    :param e: An element in [0,Q).
    """
    b = _get_xmpz(b)
    e = _get_xmpz(e)
    return ElementModQ(powmod(b, e, get_q_mpz()))


def mult_p(*elems: ElementModPOrQorInt) -> ElementModP:
    """
    Compute the product, mod p, of all elements.

    :param elems: Zero or more elements in [0,P).
    """
    product = _one_mpz
    p = get_p_mpz()
    for x in elems:
        x = _get_xmpz(x)
        product = (product * x) % p
    return ElementModP(product)


def mult_q(*elems: ElementModPOrQorInt) -> ElementModQ:
    """
    Compute the product, mod q, of all elements.

    :param elems: Zero or more elements in [0,Q).
    """
    product = _one_mpz
    q = get_q_mpz()
    for x in elems:
        x = _get_xmpz(x)
        product = (product * x) % q
    return ElementModQ(product)


def g_pow_p(e: ElementModPOrQorInt) -> ElementModP:
    """
    Compute g^e mod p.

    :param e: An element in [0,P).
    """
    return ElementModP(get_g_powradix().pow(_get_xmpz(e)))


def rand_q() -> ElementModQ:
    """
    Generate random number between 0 and Q.

    :return: Random value between 0 and Q
    """
    return ElementModQ(randbelow(get_q_mpz()))


def rand_range_q(start: ElementModQorInt) -> ElementModQ:
    """
    Generate random number between start and Q.

    :param start: Starting value of range
    :return: Random value between start and Q
    """
    start = _get_xmpz(start)
    random = 0
    while random < start:
        random = randbelow(get_q_mpz())
    return ElementModQ(random)


def get_generator_element() -> ElementModP:
    """
    Gets the generator element, g, used to generate the subgroup of elements mod P that
    correspond to valid ciphertexts in our system. If you want to use the generator
    for modular exponentiation, don't use this. Instead, use `g_pow_p`, which will be
    optimized to run significantly faster.
    """

    # Tradeoff: so long as we know we'll never use the result as the first argument
    # to pow_p(), then this is going to be faster than going through the constructor
    # of ElementModPAcceleratedPow.
    return ElementModP(get_generator())
