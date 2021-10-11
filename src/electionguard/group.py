"""Basic modular math module.

Support for basic modular math in ElectionGuard. This code's primary purpose is to be "correct",
in the sense that performance may be less than hand-optimized C code, and no guarantees are
made about timing or other side-channels.
"""

from abc import ABC
from base64 import b16decode
from secrets import randbelow
from sys import maxsize
from typing import Any, Final, Optional, Union, List

# pylint: disable=no-name-in-module
from gmpy2 import xmpz, powmod, invert

from .constants import (
    get_large_prime,
    get_small_prime,
    get_generator,
    PowRadixStyle,
    DEFAULT_POW_RADIX_STYLE,
)


class BaseElement(ABC, int):
    """An element limited by mod T within [0, T) where T is determined by an upper_bound function."""

    def __new__(cls, elem: Union[int, str], *args, **kwargs):  # type: ignore
        """Instantiate ElementModT where elem is an int or its hex representation or mpz."""

        # Using args/kwargs rather than newer named arguments to make Python's inheritance system behave.

        _ = args  # suppress warnings
        if isinstance(elem, str):
            elem = hex_to_int(elem)

        # Convoluted logic because the check request it might be a named arg, or it might be just a regular argument.
        if not(("check_within_bounds" in kwargs and not kwargs["check_within_bounds"]) or (len(args) > 0 and not args[0])):
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


# Common constants
_negative_one_mpz = xmpz(-1)
_zero_mpz = xmpz(0)
_one_mpz = xmpz(1)
_P_mpz = xmpz(get_large_prime())
_Q_mpz = xmpz(get_small_prime())


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

    def accelerate_pow(
        self, style: PowRadixStyle = PowRadixStyle.SYSTEM_DEFAULT
    ) -> "ElementModPWithFastPow":
        """
        Returns a new `ElementModPWithFastPow` that's equivalent to this `ElementModP`, but where
        modular exponentiation will go significantly faster. Does not mutate the current object.
        """
        return ElementModPWithFastPow(self, False, style)


class ElementModPWithFastPow(ElementModP):
    """
    An element that's equivalent to a regular `ElementModP`, except that when used as
    the base of a modular exponentiation, internal state will allow this computation
    to run significantly faster.
    """

    pow_radix: "PowRadix"

    def __new__(cls, elem: Union[int, str], *args, **kwargs):  # type: ignore
        # This is a hack, but it seems to be reasonably Pythonic to then go ahead and
        # store a field and treat this as the subtype, even though we're generating
        # an instance of the super-type. Some discussion of this:
        # https://stackoverflow.com/questions/10788976/how-do-i-properly-inherit-from-a-superclass-that-has-a-new-method
        return ElementModP.__new__(cls, elem, args, kwargs)

    def __init__(self, elem: Union[int, str], *args, **kwargs) -> None:  # type: ignore
        _ = args  # suppress warnings
        style: PowRadixStyle = PowRadixStyle.SYSTEM_DEFAULT
        if "style" in kwargs and isinstance(kwargs["style"], PowRadixStyle):
            style = kwargs["style"]

        self.pow_radix = PowRadix(_get_xmpz(elem), style)

    def pow_p(self, exponent: "ElementModPOrQorInt") -> "ElementModP":
        """
        Computes self ^ exponent mod p, taking advantage of the internal acceleration
        structure. Note, these two calls are equivalent::
          x = pow_p(base, exponent)
          x = base.pow_p(exponent)
        """
        return ElementModP(self.pow_radix.pow(_get_xmpz(exponent)))


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
    sum = _zero_mpz
    for e in elems:
        e = _get_xmpz(e)
        sum = (sum + e) % _Q_mpz
    return ElementModQ(sum)


def a_minus_b_q(a: ElementModQorInt, b: ElementModQorInt) -> ElementModQ:
    """Compute (a-b) mod q."""
    a = _get_xmpz(a)
    b = _get_xmpz(b)
    return ElementModQ((a - b) % _Q_mpz)


def div_p(a: ElementModPOrQorInt, b: ElementModPOrQorInt) -> ElementModP:
    """Compute a/b mod p."""
    b = _get_xmpz(b)
    inverse = invert(b, _P_mpz)
    return mult_p(a, inverse)


def div_q(a: ElementModPOrQorInt, b: ElementModPOrQorInt) -> ElementModQ:
    """Compute a/b mod q."""
    b = _get_xmpz(b)
    inverse = invert(b, _Q_mpz)
    return mult_q(a, inverse)


def negate_q(a: ElementModQorInt) -> ElementModQ:
    """Compute (Q - a) mod q."""
    a = _get_xmpz(a)
    return ElementModQ(_Q_mpz - a)


def a_plus_bc_q(
    a: ElementModQorInt, b: ElementModQorInt, c: ElementModQorInt
) -> ElementModQ:
    """Compute (a + b * c) mod q."""
    a = _get_xmpz(a)
    b = _get_xmpz(b)
    c = _get_xmpz(c)
    return ElementModQ((a + b * c) % _Q_mpz)


def mult_inv_p(e: ElementModPOrQorInt) -> ElementModP:
    """
    Compute the multiplicative inverse mod p.

    :param e:  An element in [1, P).
    """
    e = _get_xmpz(e)
    assert e != 0, "No multiplicative inverse for zero"
    tmp = powmod(e, _negative_one_mpz, _P_mpz)
    return ElementModP(tmp)


def pow_p(b: ElementModPOrQorInt, e: ElementModPOrQorInt) -> ElementModP:
    """
    Compute b^e mod p.

    :param b: An element in [0,P).
    :param e: An element in [0,P).
    """

    if isinstance(b, ElementModPWithFastPow):
        return b.pow_p(e)

    b = _get_xmpz(b)
    e = _get_xmpz(e)
    return ElementModP(powmod(b, e, _P_mpz))


def pow_q(b: ElementModQorInt, e: ElementModQorInt) -> ElementModQ:
    """
    Compute b^e mod q.

    :param b: An element in [0,Q).
    :param e: An element in [0,Q).
    """
    b = _get_xmpz(b)
    e = _get_xmpz(e)
    return ElementModQ(powmod(b, e, _Q_mpz))


def mult_p(*elems: ElementModPOrQorInt) -> ElementModP:
    """
    Compute the product, mod p, of all elements.

    :param elems: Zero or more elements in [0,P).
    """
    product = _one_mpz
    for x in elems:
        x = _get_xmpz(x)
        product = (product * x) % _P_mpz
    return ElementModP(product)


def mult_q(*elems: ElementModPOrQorInt) -> ElementModQ:
    """
    Compute the product, mod q, of all elements.

    :param elems: Zero or more elements in [0,Q).
    """
    product = _one_mpz
    for x in elems:
        x = _get_xmpz(x)
        product = (product * x) % _Q_mpz
    return ElementModQ(product)


def g_pow_p(e: ElementModPOrQorInt) -> ElementModP:
    """
    Compute g^e mod p.

    :param e: An element in [0,P).
    """
    return pow_p(get_generator_element(), e)


def rand_q() -> ElementModQ:
    """
    Generate random number between 0 and Q.

    :return: Random value between 0 and Q
    """
    return ElementModQ(randbelow(_Q_mpz))


def rand_range_q(start: ElementModQorInt) -> ElementModQ:
    """
    Generate random number between start and Q.

    :param start: Starting value of range
    :return: Random value between start and Q
    """
    start = _get_xmpz(start)
    random = 0
    while random < start:
        random = randbelow(_Q_mpz)
    return ElementModQ(random)


_G_mod_P: Optional[ElementModP] = None


def get_generator_element() -> ElementModP:
    """
    Gets the generator element, g, used to generate the subgroup of elements mod P that
    correspond to valid ciphertexts in our system.
    """
    global _G_mod_P
    if _G_mod_P is None:
        # we only want to instantiate this once, because it's going to use a lot of memory
        _G_mod_P = ElementModPWithFastPow(get_generator())
    return _G_mod_P


# Modular exponentiation performance improvements via Olivier Pereira
# https://github.com/pereira/expo-fixed-basis/blob/main/powradix.py

# Size of the exponent
_e_size = 256

# Radix method
class PowRadix:
    """Internal class, used for accelerating modular exponentiation."""

    basis: xmpz
    table_length: int
    k: int
    table: List[List[xmpz]]

    def __init__(self, basis: xmpz, style: PowRadixStyle):
        """
        The basis is to be used with future calls to the `pow` method, such that
        `PowRadix(basis).pow(e) == powmod(basis, e, P)`, except the computation
        will run much faster. By specifying which `PowRadixStyle` to use, the
        table will either use more or less memory, corresponding to greater
        acceleration.

        `PowRadixStyle.SYSTEM_DEFAULT` uses whatever the default configuration is for this installation.

        `PowRadixStyle.NO_ACCELERATION` uses no extra memory and just calls `powmod`.

        `PowRadixStyle.LOW_MEMORY_USE` corresponds to 4.2MB of state per instance of PowRadix.

        `PowRadixStyle.HIGH_MEMORY_USE` corresponds to 84MB of state per instance of PowRadix.

        `PowRadixStyle.EXTREME_MEMORY_USE` corresponds to 537MB of state per instance of PowRadix.
        """

        self.basis = basis

        if style == PowRadixStyle.SYSTEM_DEFAULT:
            style = DEFAULT_POW_RADIX_STYLE

        if style == PowRadixStyle.NO_ACCELERATION:
            self.k = 0
            return

        if style == PowRadixStyle.LOW_MEMORY_USE:
            k = 8
        elif style == PowRadixStyle.HIGH_MEMORY_USE:
            k = 13
        else:
            k = 16

        self.table_length = -(-_e_size // k)  # Double negative to take the ceiling
        self.k = k
        table: List[List[xmpz]] = []
        row_basis = basis
        running_basis = row_basis
        for _ in range(self.table_length):
            row = [_one_mpz]
            for _ in range(1, 2 ** k):
                row.append(running_basis)
                running_basis = running_basis * row_basis % _P_mpz
            table.append(row)
            row_basis = running_basis
        self.table = table

    def pow(self, e: xmpz) -> xmpz:
        e = e % _Q_mpz

        if self.k == 0:
            return powmod(self.basis, e, _P_mpz)

        y = _one_mpz
        for i in range(self.table_length):
            e_slice = e[i * self.k : (i + 1) * self.k]
            y = y * self.table[i][e_slice] % _P_mpz
        return y
