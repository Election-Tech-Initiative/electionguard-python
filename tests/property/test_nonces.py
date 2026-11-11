from unittest.mock import patch

from hypothesis import given, assume
from hypothesis.strategies import integers

from tests.base_test_case import BaseTestCase

from electionguard.group import ElementModQ, ONE_MOD_Q, TWO_MOD_Q, ZERO_MOD_Q
from electionguard.nonces import Nonces
from electionguard_tools.strategies.group import elements_mod_q


class TestNonces(BaseTestCase):
    """Nonces tests"""

    @given(elements_mod_q())
    def test_nonces_iterable(self, seed: ElementModQ):
        n = Nonces(seed)
        i = iter(n)
        q0 = next(i)
        q1 = next(i)
        self.assertTrue(q0 != q1)

    @given(elements_mod_q(), integers(min_value=0, max_value=1000000))
    def test_nonces_deterministic(self, seed: ElementModQ, i: int):
        n1 = Nonces(seed)
        n2 = Nonces(seed)
        self.assertEqual(n1[i], n2[i])

    @given(
        elements_mod_q(),
        elements_mod_q(),
    )
    def test_nonces_seed_matters(self, seed1: ElementModQ, seed2: ElementModQ):
        assume(seed1 != seed2)
        n1 = Nonces(seed1)  # pylint: disable=unreachable
        n2 = Nonces(seed2)  # pylint: disable=unreachable
        self.assertNotEqual(n1[0], n2[0])

    @given(elements_mod_q())
    def test_nonces_with_slices(self, seed: ElementModQ):
        n = Nonces(seed)
        count: int = 0
        l: list[ElementModQ] = []

        for i in iter(n):
            count += 1
            l.append(i)
            if count == 10:
                break
        self.assertEqual(len(l), 10)

        l2 = Nonces(seed)[0:10]
        self.assertEqual(len(l2), 10)
        self.assertEqual(l, l2)

    def test_nonces_type_errors(self):
        n = Nonces(ElementModQ(3))
        self.assertRaises(TypeError, len, n)
        self.assertRaises(TypeError, lambda: n[1:])
        self.assertRaises(TypeError, lambda: n.get_with_headers(-1))

    def test_nonces_skip_zero(self):
        # a third draw raises, so a repeated zero or an extra hash fails the test
        with patch(
            "electionguard.nonces.hash_elems",
            side_effect=[ZERO_MOD_Q, TWO_MOD_Q],
        ):
            self.assertEqual(Nonces(ONE_MOD_Q)[0], TWO_MOD_Q)

    def test_nonces_are_never_zero_with_small_test_constants(self):
        # with the 16 bit test Q, about 3 of these would hash to zero
        nonces = Nonces(ONE_MOD_Q)
        self.assertNotIn(ZERO_MOD_Q, nonces[0:200_000])
