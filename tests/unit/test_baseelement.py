from dataclasses import asdict, dataclass
import json

from pydantic.json import pydantic_encoder
from pydantic.tools import parse_raw_as, parse_obj_as

from tests.base_test_case import BaseTestCase

from electionguard.constants import (
    get_small_prime,
    get_large_prime,
)

from electionguard.group import (
    ElementModP,
    ElementModQ,
    ZERO_MOD_P,
    ONE_MOD_P,
    TWO_MOD_P,
    ZERO_MOD_Q,
    ONE_MOD_Q,
    TWO_MOD_Q,
)


class TestElementModQ(BaseTestCase):
    """ElementModQ tests"""

    def test_add_radd(self):
        self.assertEqual(ONE_MOD_Q + 1, TWO_MOD_Q)
        self.assertEqual(1 + ONE_MOD_Q, TWO_MOD_Q)
        self.assertEqual(ONE_MOD_Q + ONE_MOD_Q, TWO_MOD_Q)

        max_q = get_small_prime() - 1

        with self.assertRaises(OverflowError):
            _ = ElementModQ(max_q) + 1

        with self.assertRaises(OverflowError):
            _ = ElementModQ(max_q) + ONE_MOD_Q

        with self.assertRaises(OverflowError):
            _ = 1 + ElementModQ(max_q)

    def test_sub_rsub(self):
        self.assertEqual(TWO_MOD_Q - 1, ONE_MOD_Q)
        self.assertEqual(2 - ONE_MOD_Q, ONE_MOD_Q)
        self.assertEqual(TWO_MOD_Q - ONE_MOD_Q, ONE_MOD_Q)

        with self.assertRaises(OverflowError):
            _ = ZERO_MOD_Q - 1

        with self.assertRaises(OverflowError):
            _ = ZERO_MOD_Q - ONE_MOD_Q

        with self.assertRaises(OverflowError):
            _ = 0 - ONE_MOD_Q

    def test_mul_rmul(self):
        self.assertEqual(TWO_MOD_Q * 1, TWO_MOD_Q)
        self.assertEqual(1 * TWO_MOD_Q, TWO_MOD_Q)
        self.assertEqual(ONE_MOD_Q * TWO_MOD_Q, TWO_MOD_Q)

        max_q = get_small_prime() - 1
        with self.assertRaises(OverflowError):
            _ = TWO_MOD_Q * ElementModQ(max_q)

        with self.assertRaises(OverflowError):
            _ = ElementModQ(max_q) * TWO_MOD_Q

    def test_truediv_rtruediv(self):
        self.assertEqual(TWO_MOD_Q / 1, TWO_MOD_Q)
        self.assertEqual(2 / ONE_MOD_Q, TWO_MOD_Q)
        self.assertEqual(TWO_MOD_Q / ONE_MOD_Q, TWO_MOD_Q)

    def test_pow_rpow(self):
        self.assertEqual(TWO_MOD_Q ** 2, ElementModQ(4))
        self.assertEqual(2 ** TWO_MOD_Q, ElementModQ(4))
        self.assertEqual(TWO_MOD_Q ** TWO_MOD_Q, ElementModQ(4))

        max_q = get_small_prime() - 1
        with self.assertRaises(OverflowError):
            _ = max_q ** TWO_MOD_Q

    # pylint: disable=comparison-with-itself
    def test_cmp(self):
        self.assertTrue(ONE_MOD_Q < TWO_MOD_Q)
        self.assertFalse(ONE_MOD_Q < ONE_MOD_Q)
        self.assertFalse(TWO_MOD_Q < ONE_MOD_Q)

        self.assertTrue(ONE_MOD_Q <= TWO_MOD_Q)
        self.assertTrue(ONE_MOD_Q <= ONE_MOD_Q)
        self.assertFalse(TWO_MOD_Q <= ONE_MOD_Q)

        self.assertFalse(ONE_MOD_Q > TWO_MOD_Q)
        self.assertFalse(ONE_MOD_Q > ONE_MOD_Q)
        self.assertTrue(TWO_MOD_Q > ONE_MOD_Q)

        self.assertFalse(ONE_MOD_Q >= TWO_MOD_Q)
        self.assertTrue(ONE_MOD_Q >= ONE_MOD_Q)
        self.assertTrue(TWO_MOD_Q >= ONE_MOD_Q)


class TestElementModP(BaseTestCase):
    """ElementModP tests"""

    def test_add_radd(self):
        self.assertEqual(ONE_MOD_P + 1, TWO_MOD_P)
        self.assertEqual(1 + ONE_MOD_P, TWO_MOD_P)
        self.assertEqual(ONE_MOD_P + ONE_MOD_P, TWO_MOD_P)

        max_p = get_large_prime() - 1

        with self.assertRaises(OverflowError):
            _ = ElementModP(max_p) + 1

        with self.assertRaises(OverflowError):
            _ = ElementModP(max_p) + ONE_MOD_P

        with self.assertRaises(OverflowError):
            _ = 1 + ElementModP(max_p)

    def test_sub_rsub(self):
        self.assertEqual(TWO_MOD_P - 1, ONE_MOD_P)
        self.assertEqual(2 - ONE_MOD_P, ONE_MOD_P)
        self.assertEqual(TWO_MOD_P - ONE_MOD_P, ONE_MOD_P)

        with self.assertRaises(OverflowError):
            _ = ZERO_MOD_P - 1

        with self.assertRaises(OverflowError):
            _ = ZERO_MOD_P - ONE_MOD_P

        with self.assertRaises(OverflowError):
            _ = 0 - ONE_MOD_P

    def test_mul_rmul(self):
        self.assertEqual(TWO_MOD_P * 1, TWO_MOD_P)
        self.assertEqual(1 * TWO_MOD_P, TWO_MOD_P)
        self.assertEqual(ONE_MOD_P * TWO_MOD_P, TWO_MOD_P)

        max_p = get_large_prime() - 1
        with self.assertRaises(OverflowError):
            _ = TWO_MOD_P * ElementModP(max_p)

        with self.assertRaises(OverflowError):
            _ = ElementModP(max_p) * TWO_MOD_P

    def test_truediv_rtruediv(self):
        self.assertEqual(TWO_MOD_P / 1, TWO_MOD_P)
        self.assertEqual(2 / ONE_MOD_P, TWO_MOD_P)
        self.assertEqual(TWO_MOD_P / ONE_MOD_P, TWO_MOD_P)

    def test_pow_rpow(self):
        self.assertEqual(TWO_MOD_P ** 2, ElementModP(4))
        self.assertEqual(2 ** TWO_MOD_P, ElementModP(4))
        self.assertEqual(TWO_MOD_P ** TWO_MOD_P, ElementModP(4))

        max_p = get_large_prime() - 1
        with self.assertRaises(OverflowError):
            _ = max_p ** TWO_MOD_P

    # pylint: disable=comparison-with-itself
    def test_cmp(self):
        self.assertTrue(ONE_MOD_P < TWO_MOD_P)
        self.assertFalse(ONE_MOD_P < ONE_MOD_P)
        self.assertFalse(TWO_MOD_P < ONE_MOD_P)
        self.assertTrue(ONE_MOD_P < 2)
        self.assertFalse(ONE_MOD_P < 1)
        self.assertFalse(TWO_MOD_P < 1)

        self.assertTrue(ONE_MOD_P <= TWO_MOD_P)
        self.assertTrue(ONE_MOD_P <= ONE_MOD_P)
        self.assertFalse(TWO_MOD_P <= ONE_MOD_P)
        self.assertTrue(ONE_MOD_P <= 2)
        self.assertTrue(ONE_MOD_P <= 1)
        self.assertFalse(TWO_MOD_P <= 1)

        self.assertFalse(ONE_MOD_P > TWO_MOD_P)
        self.assertFalse(ONE_MOD_P > ONE_MOD_P)
        self.assertTrue(TWO_MOD_P > ONE_MOD_P)
        self.assertFalse(ONE_MOD_P > 2)
        self.assertFalse(ONE_MOD_P > 1)
        self.assertTrue(TWO_MOD_P > 1)

        self.assertFalse(ONE_MOD_P >= TWO_MOD_P)
        self.assertTrue(ONE_MOD_P >= ONE_MOD_P)
        self.assertTrue(TWO_MOD_P >= ONE_MOD_P)
        self.assertFalse(ONE_MOD_P >= 2)
        self.assertTrue(ONE_MOD_P >= 1)
        self.assertTrue(TWO_MOD_P >= 1)


@dataclass
class ElementSet:
    """Test dataclass with ElementModP and ElementModQ"""

    mod_p: ElementModP
    mod_q: ElementModQ


class TestSerializationDeserialization(BaseTestCase):
    """Serialization And Deserialization tests"""

    obj: ElementSet
    expected_dict: dict
    expected_json: str

    def setUp(self):
        super().setUp()
        p, q = 123, 124
        self.obj = ElementSet(mod_p=p, mod_q=q)
        self.expected_dict = {
            "mod_p": p,
            "mod_q": q,
        }
        self.expected_json = json.dumps(self.expected_dict, indent=4)

    def test_stdlib_serialization(self):
        self.assertEqual(self.expected_dict, asdict(self.obj))

    def test_stdlib_deserialization(self):
        self.assertEqual(self.obj, ElementSet(**self.expected_dict))

    def test_pydantic_serialization(self):
        self.assertEqual(
            self.expected_json, json.dumps(self.obj, indent=4, default=pydantic_encoder)
        )

    def test_pydantic_deserialization(self):
        self.assertEqualAsDicts(self.obj, parse_obj_as(ElementSet, self.expected_dict))
        self.assertEqualAsDicts(self.obj, parse_raw_as(ElementSet, self.expected_json))

    # pulled from tests/integration/test_end_to_end_election.py
    def assertEqualAsDicts(self, first: object, second: object):
        """
        Specialty assertEqual to compare dataclasses as dictionaries.

        This is relevant specifically to using pydantic dataclasses to import.
        Pydantic reconstructs dataclasses with name uniqueness to add their validation.
        This creates a naming issue where the default equality check fails.
        """
        self.assertEqual(asdict(first), asdict(second))
