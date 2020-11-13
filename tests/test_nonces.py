import unittest
from typing import List

from hypothesis import given, assume
from hypothesis.strategies import integers

from electionguard.group import ElementModQ, int_to_q_unchecked
from electionguard.nonces import Nonces
from electionguardtest.group import elements_mod_q


class TestNonces(unittest.TestCase):
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
        integers(min_value=0, max_value=1000000),
    )
    def test_nonces_seed_matters(self, seed1: ElementModQ, seed2: ElementModQ, i: int):
        assume(seed1 != seed2)
        n1 = Nonces(seed1)
        n2 = Nonces(seed2)
        self.assertNotEqual(n1[i], n2[i])

    @given(elements_mod_q())
    def test_nonces_with_slices(self, seed: ElementModQ):
        n = Nonces(seed)
        count: int = 0
        l: List[ElementModQ] = []

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
        n = Nonces(int_to_q_unchecked(3))
        self.assertRaises(TypeError, len, n)
        self.assertRaises(TypeError, lambda: n[1:])
        self.assertRaises(TypeError, lambda: n.get_with_headers(-1))
