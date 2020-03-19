import unittest
from typing import List

from hypothesis import given, assume

from electionguard.group import ElementModQ
from electionguard.random import RandomIterable
from tests.test_group import arb_element_mod_q


class TestRandom(unittest.TestCase):
    @given(arb_element_mod_q())
    def test_random_basics(self, seed: ElementModQ):
        r = RandomIterable(seed)
        i = iter(r)
        q0 = next(i)
        q1 = next(i)
        self.assertTrue(q0 != q1)

    @given(arb_element_mod_q())
    def test_random_basics2(self, seed: ElementModQ):
        r = RandomIterable(seed)
        q0 = r.next()
        q1 = r.next()
        self.assertTrue(q0 != q1)

    @given(arb_element_mod_q())
    def test_random_deterministic(self, seed: ElementModQ):
        r1 = RandomIterable(seed)
        r2 = RandomIterable(seed)

        self.assertEqual(r1.next(), r2.next())
        self.assertEqual(r1.next(), r2.next())
        self.assertEqual(r1.next(), r2.next())
        self.assertEqual(r1.next(), r2.next())
        self.assertEqual(r1.next(), r2.next())

    @given(arb_element_mod_q(), arb_element_mod_q())
    def test_random_seed_matters(self, seed1: ElementModQ, seed2: ElementModQ):
        assume(seed1 != seed2)
        r1 = RandomIterable(seed1)
        r2 = RandomIterable(seed2)

        self.assertNotEqual(r1.next(), r2.next())
        self.assertNotEqual(r1.next(), r2.next())
        self.assertNotEqual(r1.next(), r2.next())
        self.assertNotEqual(r1.next(), r2.next())
        self.assertNotEqual(r1.next(), r2.next())

    @given(arb_element_mod_q())
    def test_random_foreach_compat(self, seed: ElementModQ):
        r = RandomIterable(seed)
        count: int = 0
        l: List[ElementModQ] = []

        for i in r:
            count += 1
            l.append(i)
            if count == 10:
                break

        r2 = RandomIterable(seed)
        l2 = r2.take(10)

        self.assertEqual(l, l2)
