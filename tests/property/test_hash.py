from typing import List, Optional

from hypothesis import given
from hypothesis.strategies import integers


from tests.base_test_case import BaseTestCase

from electionguard.big_integer import BigInteger
from electionguard.group import ElementModP, ElementModQ
from electionguard.hash import hash_elems
from electionguard_tools.strategies.group import elements_mod_p, elements_mod_q


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

    @given(elements_mod_p(), integers(min_value=0, max_value=10))
    def test_hash_of_big_integer_with_leading_zero_bytes(
        self, input: ElementModP, multiplier: int
    ) -> None:
        """Test hashing of larger integers with leading zero bytes"""

        # Arrange.
        zero_byte = "00"
        input_hash = hash_elems(input)
        leading_zeroes = zero_byte * multiplier + input.to_hex()

        # Act.
        leading_zeroes_big_int = BigInteger(leading_zeroes)
        leading_zeroes_hash = hash_elems(leading_zeroes_big_int)

        # Assert.
        self.assertEqual(input, leading_zeroes_big_int)
        self.assertEqual(input_hash, leading_zeroes_hash)

    @given(elements_mod_p())
    def test_hash_of_big_integer_with_single_leading_zero(
        self, input: ElementModP
    ) -> None:
        """Test hashing of big integer with a single leading zero creating an invalid hex byte reprsentation."""

        # Arrange.
        invalid_hex = "0" + input.to_hex()
        input_hash = hash_elems(input)

        # Act.
        invalid_hex_big_int = BigInteger(invalid_hex)
        invalid_hex_hash = hash_elems(invalid_hex_big_int)

        # Assert.
        self.assertEqual(input, invalid_hex_big_int)
        self.assertEqual(input_hash, invalid_hex_hash)

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
