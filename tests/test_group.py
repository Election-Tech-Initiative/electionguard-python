import unittest

from hypothesis import given
from hypothesis.strategies import composite, integers

from electionguard.group import P, Q, ElementModP, ElementModQ, mult_inv_p, ONE_MOD_P, mult_mod_p, ZERO_MOD_P, G, \
    ONE_MOD_Q, g_pow, ZERO_MOD_Q, R, G_INV, in_bounds_q, in_bounds_p, in_bounds_q_no_zero, in_bounds_p_no_zero


@composite
def arb_element_mod_q(draw, elem=integers(min_value=0, max_value=Q - 1)):
    """
    Generates an arbitrary element from [0,Q).
    """
    return ElementModQ(draw(elem))


@composite
def arb_element_mod_q_no_zero(draw, elem=integers(min_value=1, max_value=Q - 1)):
    """
    Generates an arbitrary element from [1,Q).
    """
    return ElementModQ(draw(elem))


@composite
def arb_element_mod_p(draw, elem=integers(min_value=0, max_value=P - 1)):
    """
    Generates an arbitrary element from [0,P).
    """
    return ElementModP(draw(elem))


@composite
def arb_element_mod_p_no_zero(draw, elem=integers(min_value=1, max_value=P - 1)):
    """
    Generates an arbitrary element from [1,P).
    """
    return ElementModP(draw(elem))


class TestModularArithmetic(unittest.TestCase):
    def test_no_mult_inv_of_zero(self):
        self.assertRaises(Exception, mult_inv_p, ZERO_MOD_P)

    @given(arb_element_mod_p_no_zero())
    def test_mult_inverses(self, elem: ElementModP):
        inv = mult_inv_p(elem)
        self.assertEqual(mult_mod_p(elem, inv), ONE_MOD_P)

    def test_properties_for_constants(self):
        self.assertNotEqual(G, 1)
        self.assertEqual((R * Q) % P, P - 1)
        self.assertLess(Q, P)
        self.assertLess(G, P)
        self.assertLess(G_INV, P)
        self.assertLess(R, P)

    def test_simple_powers(self):
        gp = ElementModP(G)
        self.assertEqual(gp, g_pow(ONE_MOD_Q))
        self.assertEqual(ONE_MOD_P, g_pow(ZERO_MOD_Q))

    @given(arb_element_mod_q())
    def test_in_bounds_q(self, q: ElementModQ):
        self.assertTrue(in_bounds_q(q))
        self.assertFalse(in_bounds_q(ElementModQ(q.elem + Q)))
        self.assertFalse(in_bounds_q(ElementModQ(q.elem - Q)))

    @given(arb_element_mod_p())
    def test_in_bounds_p(self, p: ElementModP):
        self.assertTrue(in_bounds_p(p))
        self.assertFalse(in_bounds_p(ElementModP(p.elem + P)))
        self.assertFalse(in_bounds_p(ElementModP(p.elem - P)))

    @given(arb_element_mod_q_no_zero())
    def test_in_bounds_q_no_zero(self, q: ElementModQ):
        self.assertTrue(in_bounds_q_no_zero(q))
        self.assertFalse(in_bounds_q_no_zero(ElementModQ(q.elem + Q)))
        self.assertFalse(in_bounds_q_no_zero(ElementModQ(q.elem - Q)))

    @given(arb_element_mod_p_no_zero())
    def test_in_bounds_p_no_zero(self, p: ElementModP):
        self.assertTrue(in_bounds_p_no_zero(p))
        self.assertFalse(in_bounds_p_no_zero(ElementModP(p.elem + P)))
        self.assertFalse(in_bounds_p_no_zero(ElementModP(p.elem - P)))
