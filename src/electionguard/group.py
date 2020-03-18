# Support for basic modular math in ElectionGuard. This code's primary purpose is to be "correct",
# in the sense that performance may be less than hand-optimized C code, and no guarantees are
# made about timing or other side-channels.

from typing import Final, Union, NamedTuple

# Constants used by ElectionGuard
Q: Final[int] = pow(2, 256) - 189
P: Final[int] = pow(2, 4096) - 69 * Q - 2650872664557734482243044168410288960
R: Final[int] = ((P - 1) * pow(Q, -1, P)) % P
G: Final[int] = pow(2, R, P)
G_INV: Final[int] = pow(G, -1, P)


class ElementModQ(NamedTuple):
    """An element of the smaller `mod q` space, i.e., in [0, Q), where Q is a 256-bit prime."""
    elem: int


ZERO_MOD_Q: Final[ElementModQ] = ElementModQ(0)
ONE_MOD_Q: Final[ElementModQ] = ElementModQ(1)
TWO_MOD_Q: Final[ElementModQ] = ElementModQ(2)


class ElementModP(NamedTuple):
    """An element of the larger `mod p` space, i.e., in [0, P), where P is a 4096-bit prime."""
    elem: int


ZERO_MOD_P: Final[ElementModP] = ElementModP(0)
ONE_MOD_P: Final[ElementModP] = ElementModP(1)
TWO_MOD_P: Final[ElementModP] = ElementModP(2)

ElementModPOrQ = Union[ElementModP, ElementModQ]  # generally useful typedef


def int_to_q(i: int) -> ElementModQ:
    """
    Given a Python integer, returns an ElementModQ.
    Raises an exception if it's out of bounds.
    """
    if 0 <= i < Q:
        return ElementModQ(i)
    else:
        raise Exception("given element doesn't fit in Q: " + str(i))


def int_to_q_unchecked(i: int) -> ElementModQ:
    """
    Given a Python integer, returns an ElementModQ. Allows
    for the input to be out-of-bounds, and thus creating an invalid
    element (i.e., outside of [0,Q)). Useful for tests.
    Don't use anywhere else.
    """
    return ElementModQ(i)


def int_to_p(i: int) -> ElementModP:
    """
    Given a Python integer, returns an ElementModP.
    Raises an exception if it's out of bounds.
    """
    if 0 <= i < P:
        return ElementModP(i)
    else:
        raise Exception("given element doesn't fit in P: " + str(i))


def int_to_p_unchecked(i: int) -> ElementModP:
    """
    Given a Python integer, returns an ElementModP. Allows
    for the input to be out-of-bounds, and thus creating an invalid
    element (i.e., outside of [0,P)). Useful for tests.
    Don't use anywhere else.
    """
    return ElementModP(i)


def elem_to_int(a: ElementModPOrQ) -> int:
    """
    Given an ElementModP or ElementModP, returns a regular Python integer.
    """
    return a.elem


def add_q(*elems: ElementModQ) -> ElementModQ:
    """
    Adds together one or more elements in Q, returns the sum mod Q.
    """
    t = 0
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
    Computes (a + b * c) mod q
    """
    return ElementModQ((a.elem + b.elem * c.elem) % Q)


def mult_inv_p(e: ElementModPOrQ) -> ElementModP:
    """
    Computes the multiplicative inverse mod p.
    :param e:  An element in [1, P).
    """
    if e.elem == 0:
        raise Exception("No multiplicative inverse for zero")
    return ElementModP(pow(e.elem, -1, P))


def pow_p(b: ElementModPOrQ, e: ElementModPOrQ) -> ElementModP:
    """
    Computes b^e mod p.
    :param b: An element in [0,P).
    :param e: An element in [0,P).
    """
    return ElementModP(pow(b.elem, e.elem, P))


def mult_p(*elems: ElementModPOrQ) -> ElementModP:
    """
    Computes the product, mod p, of all elements.
    :param elems: Zero or more elements in [0,P).
    """
    product = ONE_MOD_P
    for x in elems:
        product = ElementModP((product.elem * x.elem) % P)
    return product


def g_pow_p(e: ElementModPOrQ) -> ElementModP:
    """
    Computes g^e mod p.
    :param e: An element in [0,P).
    """
    return pow_p(ElementModP(G), e)


def in_bounds_p(p: ElementModP) -> bool:
    """
    Validates that the element is actually within the bounds of [0,P).
    Returns true if all is good, false if something's wrong.
    """
    return 0 <= p.elem < P


def in_bounds_q(q: ElementModQ) -> bool:
    """
    Validates that the element is actually within the bounds of [0,Q).
    Returns true if all is good, false if something's wrong.
    """
    return 0 <= q.elem < Q


def in_bounds_p_no_zero(p: ElementModP) -> bool:
    """
    Validates that the element is actually within the bounds of [1,P).
    Returns true if all is good, false if something's wrong.
    """
    return 0 < p.elem < P


def in_bounds_q_no_zero(q: ElementModQ) -> bool:
    """
    Validates that the element is actually within the bounds of [1,Q).
    Returns true if all is good, false if something's wrong.
    """
    return 0 < q.elem < Q


def valid_residue(x: ElementModP) -> bool:
    """
    Validates that x is in Z^r_p.
    Returns true if all is good, false if something's wrong.
    """
    bounds = 0 <= x.elem < P
    residue = pow_p(x, ElementModQ(Q)) == ONE_MOD_P
    return bounds and residue
