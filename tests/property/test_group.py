from typing import Optional

from hypothesis import given

from tests.base_test_case import BaseTestCase

from electionguard.constants import (
    get_small_prime,
    get_large_prime,
    get_generator,
    get_cofactor,
)
from electionguard.group import (
    ElementModP,
    ElementModQ,
    a_minus_b_q,
    mult_inv_p,
    ONE_MOD_P,
    mult_p,
    ZERO_MOD_P,
    ONE_MOD_Q,
    g_pow_p,
    ZERO_MOD_Q,
    int_to_p,
    int_to_q,
    add_q,
    div_q,
    div_p,
    a_plus_bc_q,
)
from electionguard.utils import (
    flatmap_optional,
    get_or_else_optional,
    match_optional,
    get_optional,
)
from electionguard_tools.strategies.group import (
    elements_mod_p_no_zero,
    elements_mod_p,
    elements_mod_q,
    elements_mod_q_no_zero,
)


class TestEquality(BaseTestCase):
    """Math equality tests"""

    @given(elements_mod_q(), elements_mod_q())
    def test_p_not_equal_to_q(self, q: ElementModQ, q2: ElementModQ):
        p = ElementModP(q)
        p2 = ElementModP(q2)

        # same value should imply they're equal
        self.assertEqual(p, q)
        self.assertEqual(q, p)

        if q != q2:
            # these are genuinely different numbers
            self.assertNotEqual(q, q2)
            self.assertNotEqual(p, p2)
            self.assertNotEqual(q, p2)
            self.assertNotEqual(p, q2)

        # of course, we're going to make sure that a number is equal to itself
        self.assertEqual(p, p)
        self.assertEqual(q, q)


class TestModularArithmetic(BaseTestCase):
    """Math Modular Arithmetic tests"""

    @given(elements_mod_q())
    def test_add_q(self, q: ElementModQ):
        as_int = add_q(q, 1)
        as_elem = add_q(q, ElementModQ(1))
        self.assertEqual(as_int, as_elem)

    @given(elements_mod_q())
    def test_a_plus_bc_q(self, q: ElementModQ):
        as_int = a_plus_bc_q(q, 1, 1)
        as_elem = a_plus_bc_q(q, ElementModQ(1), ElementModQ(1))
        self.assertEqual(as_int, as_elem)

    @given(elements_mod_q())
    def test_a_minus_b_q(self, q: ElementModQ):
        as_int = a_minus_b_q(q, 1)
        as_elem = a_minus_b_q(q, ElementModQ(1))
        self.assertEqual(as_int, as_elem)

    @given(elements_mod_q())
    def test_div_q(self, q: ElementModQ):
        as_int = div_q(q, 1)
        as_elem = div_q(q, ElementModQ(1))
        self.assertEqual(as_int, as_elem)

    @given(elements_mod_p())
    def test_div_p(self, p: ElementModQ):
        as_int = div_p(p, 1)
        as_elem = div_p(p, ElementModP(1))
        self.assertEqual(as_int, as_elem)

    def test_no_mult_inv_of_zero(self):
        self.assertRaises(Exception, mult_inv_p, ZERO_MOD_P)

    @given(elements_mod_p_no_zero())
    def test_mult_inverses(self, elem: ElementModP):
        inv = mult_inv_p(elem)
        self.assertEqual(mult_p(elem, inv), ONE_MOD_P)

    @given(elements_mod_p())
    def test_mult_identity(self, elem: ElementModP):
        self.assertEqual(elem, mult_p(elem))

    def test_mult_noargs(self):
        self.assertEqual(ONE_MOD_P, mult_p())

    def test_add_noargs(self):
        self.assertEqual(ZERO_MOD_Q, add_q())

    def test_properties_for_constants(self):
        self.assertNotEqual(get_generator(), 1)
        self.assertEqual(
            (get_cofactor() * get_small_prime()) % get_large_prime(),
            get_large_prime() - 1,
        )
        self.assertLess(get_small_prime(), get_large_prime())
        self.assertLess(get_generator(), get_large_prime())
        self.assertLess(get_cofactor(), get_large_prime())

    def test_simple_powers(self):
        gp = int_to_p(get_generator())
        self.assertEqual(gp, g_pow_p(ONE_MOD_Q))
        self.assertEqual(ONE_MOD_P, g_pow_p(ZERO_MOD_Q))

    @given(elements_mod_q())
    def test_in_bounds_q(self, q: ElementModQ):
        self.assertTrue(q.is_in_bounds())
        too_big = q + get_small_prime()
        too_small = q - get_small_prime()
        self.assertFalse(ElementModQ(too_big, False).is_in_bounds())
        self.assertFalse(ElementModQ(too_small, False).is_in_bounds())
        self.assertEqual(None, int_to_q(too_big))
        self.assertEqual(None, int_to_q(too_small))
        with self.assertRaises(OverflowError):
            ElementModQ(too_big)
        with self.assertRaises(OverflowError):
            ElementModQ(too_small)

    @given(elements_mod_p())
    def test_in_bounds_p(self, p: ElementModP):
        self.assertTrue(p.is_in_bounds())
        too_big = p + get_large_prime()
        too_small = p - get_large_prime()
        self.assertFalse(ElementModP(too_big, False).is_in_bounds())
        self.assertFalse(ElementModP(too_small, False).is_in_bounds())
        self.assertEqual(None, int_to_p(too_big))
        self.assertEqual(None, int_to_p(too_small))
        with self.assertRaises(OverflowError):
            ElementModP(too_big)
        with self.assertRaises(OverflowError):
            ElementModP(too_small)

    @given(elements_mod_q_no_zero())
    def test_in_bounds_q_no_zero(self, q: ElementModQ):
        self.assertTrue(q.is_in_bounds_no_zero())
        self.assertFalse(ZERO_MOD_Q.is_in_bounds_no_zero())
        self.assertFalse(
            ElementModQ(q + get_small_prime(), False).is_in_bounds_no_zero()
        )
        self.assertFalse(
            ElementModQ(q - get_small_prime(), False).is_in_bounds_no_zero()
        )

    @given(elements_mod_p_no_zero())
    def test_in_bounds_p_no_zero(self, p: ElementModP):
        self.assertTrue(p.is_in_bounds_no_zero())
        self.assertFalse(ZERO_MOD_P.is_in_bounds_no_zero())
        self.assertFalse(
            ElementModP(p + get_large_prime(), False).is_in_bounds_no_zero()
        )
        self.assertFalse(
            ElementModP(p - get_large_prime(), False).is_in_bounds_no_zero()
        )

    @given(elements_mod_q())
    def test_large_values_rejected_by_int_to_q(self, q: ElementModQ):
        oversize = q + get_small_prime()
        self.assertEqual(None, int_to_q(oversize))


class TestOptionalFunctions(BaseTestCase):
    """Math Optional Functions tests"""

    def test_unwrap(self):
        good: Optional[int] = 3
        bad: Optional[int] = None

        self.assertEqual(get_optional(good), 3)
        self.assertRaises(Exception, get_optional, bad)

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

        self.assertEqual(5, get_optional(flatmap_optional(good, lambda x: x + 2)))
        self.assertIsNone(flatmap_optional(bad, lambda x: x + 2))
