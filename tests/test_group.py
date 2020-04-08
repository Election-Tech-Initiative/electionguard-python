import unittest
from typing import Optional

from hypothesis import given
from hypothesis.strategies import composite, integers

from electionguard.group import (
    P,
    Q,
    ElementModP,
    ElementModQ,
    mult_inv_p,
    ONE_MOD_P,
    mult_p,
    ZERO_MOD_P,
    G,
    ONE_MOD_Q,
    g_pow_p,
    ZERO_MOD_Q,
    R,
    G_INV,
    in_bounds_q,
    in_bounds_p,
    in_bounds_q_no_zero,
    in_bounds_p_no_zero,
    int_to_p,
    int_to_q,
    elem_to_int,
    add_q,
    int_to_p_unchecked,
    int_to_q_unchecked,
    unwrap_optional,
    match_optional,
    get_or_else_optional,
    flatmap_optional,
)


@composite
def arb_element_mod_q(draw, elem=integers(min_value=0, max_value=Q - 1)):
    """
    Generates an arbitrary element from [0,Q).
    """
    return int_to_q(draw(elem))


@composite
def arb_element_mod_q_no_zero(draw, elem=integers(min_value=1, max_value=Q - 1)):
    """
    Generates an arbitrary element from [1,Q).
    """
    return int_to_q(draw(elem))


@composite
def arb_element_mod_p(draw, elem=integers(min_value=0, max_value=P - 1)):
    """
    Generates an arbitrary element from [0,P).
    """
    return int_to_p(draw(elem))


@composite
def arb_element_mod_p_no_zero(draw, elem=integers(min_value=1, max_value=P - 1)):
    """
    Generates an arbitrary element from [1,P).
    """
    return int_to_p(draw(elem))


class TestModularArithmetic(unittest.TestCase):
    def test_no_mult_inv_of_zero(self):
        self.assertRaises(Exception, mult_inv_p, ZERO_MOD_P)

    @given(arb_element_mod_p_no_zero())
    def test_mult_inverses(self, elem: ElementModP):
        inv = mult_inv_p(elem)
        self.assertEqual(mult_p(elem, inv), ONE_MOD_P)

    @given(arb_element_mod_p())
    def test_mult_identity(self, elem: ElementModP):
        self.assertEqual(elem, mult_p(elem))

    def test_mult_noargs(self):
        self.assertEqual(ONE_MOD_P, mult_p())

    def test_add_noargs(self):
        self.assertEqual(ZERO_MOD_Q, add_q())

    def test_properties_for_constants(self):
        self.assertNotEqual(G, 1)
        self.assertEqual((R * Q) % P, P - 1)
        self.assertLess(Q, P)
        self.assertLess(G, P)
        self.assertLess(G_INV, P)
        self.assertLess(R, P)

    def test_simple_powers(self):
        gp = int_to_p(G)
        self.assertEqual(gp, g_pow_p(ONE_MOD_Q))
        self.assertEqual(ONE_MOD_P, g_pow_p(ZERO_MOD_Q))

    @given(arb_element_mod_q())
    def test_in_bounds_q(self, q: ElementModQ):
        self.assertTrue(in_bounds_q(q))
        too_big = elem_to_int(q) + Q
        too_small = elem_to_int(q) - Q
        self.assertFalse(in_bounds_q(int_to_q_unchecked(too_big)))
        self.assertFalse(in_bounds_q(int_to_q_unchecked(too_small)))
        self.assertEqual(None, int_to_q(too_big))
        self.assertEqual(None, int_to_q(too_small))

    @given(arb_element_mod_p())
    def test_in_bounds_p(self, p: ElementModP):
        self.assertTrue(in_bounds_p(p))
        too_big = elem_to_int(p) + P
        too_small = elem_to_int(p) - P
        self.assertFalse(in_bounds_p(int_to_p_unchecked(too_big)))
        self.assertFalse(in_bounds_p(int_to_p_unchecked(too_small)))
        self.assertEqual(None, int_to_p(too_big))
        self.assertEqual(None, int_to_p(too_small))

    @given(arb_element_mod_q_no_zero())
    def test_in_bounds_q_no_zero(self, q: ElementModQ):
        self.assertTrue(in_bounds_q_no_zero(q))
        self.assertFalse(in_bounds_q_no_zero(ZERO_MOD_Q))
        self.assertFalse(in_bounds_q_no_zero(int_to_q_unchecked(elem_to_int(q) + Q)))
        self.assertFalse(in_bounds_q_no_zero(int_to_q_unchecked(elem_to_int(q) - Q)))

    @given(arb_element_mod_p_no_zero())
    def test_in_bounds_p_no_zero(self, p: ElementModP):
        self.assertTrue(in_bounds_p_no_zero(p))
        self.assertFalse(in_bounds_p_no_zero(ZERO_MOD_P))
        self.assertFalse(in_bounds_p_no_zero(int_to_p_unchecked(elem_to_int(p) + P)))
        self.assertFalse(in_bounds_p_no_zero(int_to_p_unchecked(elem_to_int(p) - P)))


class TestOptionalFunctions(unittest.TestCase):
    def test_unwrap(self):
        good: Optional[int] = 3
        bad: Optional[int] = None

        self.assertEqual(unwrap_optional(good), 3)
        self.assertRaises(Exception, unwrap_optional, bad)

    def test_match(self):
        good: Optional[int] = 3
        bad: Optional[int] = None

        self.assertEqual(5, match_optional(good, lambda: 1, lambda x: x + 2))
        self.assertEqual(1, match_optional(bad, lambda: 1, lambda x: x + 2))

    def test_get_or_else(self):
        good: Optional[int] = 3
        bad: Optional[int] = None

        self.assertEqual(3, get_or_else_optional(good, 5))
        self.assertEqual(5, get_or_else_optional(bad, 5))

    def test_flatmap(self):
        good: Optional[int] = 3
        bad: Optional[int] = None

        self.assertEqual(5, unwrap_optional(flatmap_optional(good, lambda x: x + 2)))
        self.assertIsNone(flatmap_optional(bad, lambda x: x + 2))
