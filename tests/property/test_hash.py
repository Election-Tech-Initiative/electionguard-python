from typing import List, Optional

from hypothesis import given

from tests.base_test_case import BaseTestCase
from tests.property.test_group import elements_mod_p, elements_mod_q

from electionguard.group import ElementModQ
from electionguard.hash import hash_elems


class TestHash(BaseTestCase):
    """Hash tests"""

    @given(elements_mod_p(), elements_mod_q())
    def test_same_answer_twice_in_a_row(self, a: ElementModQ, b: ElementModQ):
        # if this doesn't work, then our hash function isn't a function
        h1 = hash_elems(a, b)
        h2 = hash_elems(a, b)
        self.assertEqual(h1, h2)

    @given(elements_mod_q(), elements_mod_q())
    def test_basic_hash_properties(self, a: ElementModQ, b: ElementModQ):
        ha = hash_elems(a)
        hb = hash_elems(b)
        if a == b:
            self.assertEqual(ha, hb)
        if ha != hb:
            self.assertNotEqual(a, b)

    def test_hash_for_zero_number_is_zero_string(self):
        self.assertEqual(hash_elems(0), hash_elems("0"))

    def test_hash_for_non_zero_number_string_same_as_explicit_number(self):
        self.assertEqual(hash_elems(1), hash_elems("1"))

    def test_different_strings_casing_not_the_same_hash(self):
        self.assertNotEqual(
            hash_elems("Welcome To ElectionGuard"),
            hash_elems("welcome to electionguard"),
        )

    def test_hash_for_none_same_as_null_string(self):
        self.assertEqual(hash_elems(None), hash_elems("null"))

    def test_hash_of_save_values_in_list_are_same_hash(self):
        self.assertEqual(hash_elems(["0", "0"]), hash_elems(["0", "0"]))

    def test_hash_null_equivalents(self):
        null_list: Optional[List[str]] = None
        empty_list: List[str] = []

        self.assertEqual(hash_elems(null_list), hash_elems(empty_list))
        self.assertEqual(hash_elems(empty_list), hash_elems(None))
        self.assertEqual(hash_elems(empty_list), hash_elems("null"))

    def test_hash_not_null_equivalents(self):
        self.assertNotEqual(hash_elems(None), hash_elems(""))
        self.assertNotEqual(hash_elems(None), hash_elems(0))

    def test_hash_value_from_nested_list_and_result_of_hashed_list_by_taking_the_hex(
        self,
    ):
        nested_hash = hash_elems(["0", "1"], "3")
        non_nested_1 = hash_elems("0", "1")
        non_nested_2 = hash_elems(non_nested_1.to_hex(), "3")

        self.assertNotEqual(nested_hash, non_nested_1)
        self.assertEqual(nested_hash, non_nested_2)
