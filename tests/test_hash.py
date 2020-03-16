import unittest

from hypothesis import given

from electionguard.hash import hash_two_elems_mod_q
from tests.test_group import arb_element_mod_p


class TestHash(unittest.TestCase):
    @given(arb_element_mod_p(), arb_element_mod_p())
    def test_same_answer_twice_in_a_row(self, a, b):
        # if this doesn't work, then our hash function isn't a function
        h1 = hash_two_elems_mod_q(a, b)
        h2 = hash_two_elems_mod_q(a, b)
        self.assertEqual(h1, h2)
