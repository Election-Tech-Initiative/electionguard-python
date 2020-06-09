# Support for basic modular math in ElectionGuard. This code's primary purpose is to be "correct",
# in the sense that performance may be less than hand-optimized C code, and no guarantees are
# made about timing or other side-channels.

from typing import Final, Union, NamedTuple, Optional, Any

from gmpy2 import mpz, powmod, to_binary, from_binary

# Constants used by ElectionGuard
Q: Final[int] = pow(2, 256) - 189
P: Final[int] = pow(2, 4096) - 69 * Q - 2650872664557734482243044168410288960
R: Final[int] = ((P - 1) * pow(Q, -1, P)) % P
G: Final[int] = pow(2, R, P)
G_INV: Final[int] = pow(G, -1, P)
Q_MINUS_ONE: Final[int] = Q - 1


class ElementModQ(NamedTuple):
    """An element of the smaller `mod q` space, i.e., in [0, Q), where Q is a 256-bit prime."""

    elem: mpz

    def to_int(self) -> int:
        """
        Converts from the element to a regular integer. This is preferable to directly
        accessing `elem`, whose representation might change.
        """
        return self.elem

    def is_in_bounds(self) -> bool:
        """
        Validates that the element is actually within the bounds of [0,Q).
        Returns true if all is good, false if something's wrong.
        """
        return 0 <= self.elem < Q

    def is_in_bounds_no_zero(self) -> bool:
        """
        Validates that the element is actually within the bounds of [1,Q).
        Returns true if all is good, false if something's wrong.
        """
        return 0 < self.elem < Q

    # overload != (not equal to) operator
    def __ne__(self, other: Any) -> bool:
        return (
            isinstance(other, ElementModP) or isinstance(other, ElementModQ)
        ) and not eq_elems(self, other)

    # overload == (equal to) operator
    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, ElementModP) or isinstance(other, ElementModQ)
        ) and eq_elems(self, other)


class ElementModP(NamedTuple):
    """An element of the larger `mod p` space, i.e., in [0, P), where P is a 4096-bit prime."""

    elem: mpz

    def to_int(self) -> int:
        """
        Converts from the element to a regular integer. This is preferable to directly
        accessing `elem`, whose representation might change.
        """
        return self.elem

    def is_in_bounds(self) -> bool:
        """
        Validates that the element is actually within the bounds of [0,P).
        Returns true if all is good, false if something's wrong.
        """
        return 0 <= self.elem < P

    def is_in_bounds_no_zero(self) -> bool:
        """
        Validates that the element is actually within the bounds of [1,P).
        Returns true if all is good, false if something's wrong.
        """
        return 0 < self.elem < P

    def is_valid_residue(self) -> bool:
        """
        Validates that this element is in Z^r_p.
        Returns true if all is good, false if something's wrong.
        """
        residue = pow_p(self, ElementModQ(mpz(Q))) == ONE_MOD_P
        return self.is_in_bounds() and residue

    # overload != (not equal to) operator
    def __ne__(self, other: Any) -> bool:
        return (
            isinstance(other, ElementModP) or isinstance(other, ElementModQ)
        ) and not eq_elems(self, other)

    # overload == (equal to) operator
    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, ElementModP) or isinstance(other, ElementModQ)
        ) and eq_elems(self, other)


# Handy constants. Defined once, so we can avoid allocating lots of copies.
ZERO_MOD_Q: Final[ElementModQ] = ElementModQ(mpz(0))
ONE_MOD_Q: Final[ElementModQ] = ElementModQ(mpz(1))
TWO_MOD_Q: Final[ElementModQ] = ElementModQ(mpz(2))

ZERO_MOD_P: Final[ElementModP] = ElementModP(mpz(0))
ONE_MOD_P: Final[ElementModP] = ElementModP(mpz(1))
TWO_MOD_P: Final[ElementModP] = ElementModP(mpz(2))

ElementModPOrQ = Union[ElementModP, ElementModQ]  # generally useful typedef


def int_to_q(i: int) -> Optional[ElementModQ]:
    """
    Given a Python integer, returns an ElementModQ.
    Returns `None` if the number is out of the allowed
    [0,Q) range.
    """
    if 0 <= i < Q:
        return ElementModQ(mpz(i))
    else:
        return None


def int_to_q_unchecked(i: int) -> ElementModQ:
    """
    Given a Python integer, returns an ElementModQ. Allows
    for the input to be out-of-bounds, and thus creating an invalid
    element (i.e., outside of [0,Q)). Useful for tests of it
    you're absolutely, positively, certain the input is in-bounds.
    """

    return ElementModQ(mpz(i))


def int_to_p(i: int) -> Optional[ElementModP]:
    """
    Given a Python integer, returns an ElementModP.
    Returns `None` if the number is out of the allowed
    [0,P) range.
    """
    if 0 <= i < P:
        return ElementModP(mpz(i))
    else:
        return None


def int_to_p_unchecked(i: int) -> ElementModP:
    """
    Given a Python integer, returns an ElementModP. Allows
    for the input to be out-of-bounds, and thus creating an invalid
    element (i.e., outside of [0,P)). Useful for tests or if
    you're absolutely, positively, certain the input is in-bounds.
    """
    return ElementModP(mpz(i))


def q_to_bytes(e: ElementModQ) -> bytes:
    """
    Returns a byte sequence from the element.
    """
    return to_binary(e.elem)


def bytes_to_q(b: bytes) -> ElementModQ:
    """
    Returns an element from a byte sequence.
    """
    return ElementModQ(mpz(from_binary(b)))


def add_q(*elems: ElementModQ) -> ElementModQ:
    """
    Adds together one or more elements in Q, returns the sum mod Q.
    """
    t = mpz(0)
    for e in elems:
        t = (t + e.elem) % Q

    return ElementModQ(t)


def a_minus_b_q(a: ElementModQ, b: ElementModQ) -> ElementModQ:
    """
    Computes (a-b) mod q.
    """
    return ElementModQ((a.elem - b.elem) % Q)


def negate_q(a: ElementModQ) -> ElementModQ:
    """
    Computes (Q - a) mod q.
    """
    return ElementModQ(Q - a.elem)


def a_plus_bc_q(a: ElementModQ, b: ElementModQ, c: ElementModQ) -> ElementModQ:
    """
    Computes (a + b * c) mod q.
    """
    return ElementModQ((a.elem + b.elem * c.elem) % Q)


def mult_inv_p(e: ElementModPOrQ) -> ElementModP:
    """
    Computes the multiplicative inverse mod p.

    :param e:  An element in [1, P).
    """
    assert e.elem != 0, "No multiplicative inverse for zero"
    return ElementModP(powmod(e.elem, -1, P))


def pow_p(b: ElementModPOrQ, e: ElementModPOrQ) -> ElementModP:
    """
    Computes b^e mod p.

    :param b: An element in [0,P).
    :param e: An element in [0,P).
    """
    return ElementModP(powmod(b.elem, e.elem, P))


def mult_p(*elems: ElementModPOrQ) -> ElementModP:
    """
    Computes the product, mod p, of all elements.

    :param elems: Zero or more elements in [0,P).
    """
    product = mpz(1)
    for x in elems:
        product = (product * x.elem) % P
    return ElementModP(product)


def g_pow_p(e: ElementModPOrQ) -> ElementModP:
    """
    Computes g^e mod p.

    :param e: An element in [0,P).
    """
    return pow_p(ElementModP(mpz(G)), e)


def eq_elems(a: ElementModPOrQ, b: ElementModPOrQ) -> bool:
    """
    Returns whether the two elements hold the same value.
    """
    return a.elem == b.elem
