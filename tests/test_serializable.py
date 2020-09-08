from unittest import TestCase
from os import remove

from electionguard.serializable import (
    set_deserializers,
    set_serializers,
    write_json_file,
    write_json_object,
    write_json,
)


class TestSerializable(TestCase):
    def test_write_json(self) -> None:
        # Arrange
        json_data = {
            "from_json_file": {},
            "test": 1,
            "nested": {"from_json_file": {}, "test": 1},
            "array": [{"from_json_file": {}, "test": 1}],
        }
        expected_json_string = (
            '{"test": 1, "nested": {"test": 1}, "array": [{"test": 1}]}'
        )

        # Act
        json_string = write_json(json_data)

        # Assert
        self.assertEqual(json_string, expected_json_string)

    def test_write_json_object(self) -> None:
        # Arrange
        json_data = {
            "from_json_file": {},
            "test": 1,
            "nested": {"from_json_file": {}, "test": 1},
            "array": [{"from_json_file": {}, "test": 1}],
        }
        expected_json_object = {
            "test": 1,
            "nested": {"test": 1},
            "array": [{"test": 1}],
        }

        # Act
        json_object = write_json_object(json_data)

        # Assert
        self.assertEqual(json_object, expected_json_object)

    def test_write_json_file(self) -> None:
        # Arrange
        json_data = {
            "from_json_file": {},
            "test": 1,
            "nested": {"from_json_file": {}, "test": 1},
            "array": [{"from_json_file": {}, "test": 1}],
        }
        expected_json_data = (
            '{"test": 1, "nested": {"test": 1}, "array": [{"test": 1}]}'
        )
        file_name = "json_write_test"
        json_file = file_name + ".json"

        # Act
        write_json_file(json_data, file_name)

        # Assert
        with open(json_file) as reader:
            self.assertEqual(reader.read(), expected_json_data)

        # Cleanup
        remove(json_file)

    def test_setup_serialization(self) -> None:
        # Act
        set_serializers()

    def test_setup_deserialization(self) -> None:
        # Act
        set_deserializers()
