from dataclasses import dataclass
from os import remove
from unittest import TestCase

from hypothesis import given
from hypothesis.strategies import integers

from electionguard.election import ElectionConstants
from electionguard.group import ElementModP
from electionguard.serializable import (
    set_deserializers,
    set_serializers,
    write_json_file,
    maybe_base64_to_int,
    int_to_base64_maybe,
    Serializable,
    ENCODE_THRESHOLD,
)
from electionguardtest.group import elements_mod_p


@dataclass(eq=True)
class BigAndSmall(Serializable):
    small: int
    big: int


class TestSerializable(TestCase):
    def setUp(self) -> None:
        set_serializers()
        set_deserializers()

    def test_write_json_file(self) -> None:
        # Arrange
        json_data = '{ "test" : 1 }'
        file_name = "json_write_test"
        json_file = file_name + ".json"

        # Act
        write_json_file(json_data, file_name)

        # Assert
        with open(json_file) as reader:
            self.assertEqual(reader.read(), json_data)

        # Cleanup
        remove(json_file)

    @given(elements_mod_p())
    def test_base64_conversions(self, p: ElementModP) -> None:
        i = p.to_int()
        self.assertEqual(i, maybe_base64_to_int(int_to_base64_maybe(i)))

    def test_election_constants_serialization(self) -> None:
        # ElectionConstants has large integers that we want to encode
        expected = ElectionConstants()
        expected_json = expected.to_json()
        actual = ElectionConstants.from_json(expected_json)
        self.assertEqual(expected, actual)

    @given(
        integers(0, ENCODE_THRESHOLD - 1),
        integers(ENCODE_THRESHOLD, 1000 * ENCODE_THRESHOLD),
    )
    def test_big_and_small_serialization(self, small: int, big: int) -> None:
        expected = BigAndSmall(small, big)
        expected_json = expected.to_json()
        actual = BigAndSmall.from_json(expected_json)
        self.assertEqual(expected, actual)
