from dataclasses import dataclass
from unittest import TestCase
from typing import Any, List, Optional
from os import remove

from electionguard.serializable import (
    set_deserializers,
    set_serializers,
    read_json,
    read_json_file,
    read_json_object,
    write_json,
    write_json_file,
    write_json_object,
)


@dataclass
class NestedModel:
    """Nested model for testing"""

    test: int
    from_json_file: Optional[Any] = None


@dataclass
class DataModel:
    """Data model for testing"""

    test: int
    nested: NestedModel
    array: List[NestedModel]
    from_json_file: Optional[Any] = None


JSON_DATA: DataModel = DataModel(
    test=1, nested=NestedModel(test=1), array=[NestedModel(test=1)]
)
EXPECTED_JSON_STRING = '{"array": [{"test": 1}], "nested": {"test": 1}, "test": 1}'
EXPECTED_JSON_OBJECT = {
    "test": 1,
    "nested": {"test": 1},
    "array": [{"test": 1}],
}


class TestSerializable(TestCase):
    def test_read_and_write_json(self) -> None:
        # Act
        json_string = write_json(JSON_DATA)

        # Assert
        self.assertEqual(json_string, EXPECTED_JSON_STRING)

        # Act
        read_json_data = read_json(json_string, DataModel)

        # Assert
        self.assertEqual(read_json_data, JSON_DATA)

    def test_read_and_write_json_object(self) -> None:
        # Act
        json_object = write_json_object(JSON_DATA)

        # Assert
        self.assertEqual(json_object, EXPECTED_JSON_OBJECT)

        # Act
        read_json_data = read_json_object(json_object, DataModel)

        # Assert
        self.assertEqual(read_json_data, JSON_DATA)

    def test_read_and_write_json_file(self) -> None:
        # Arrange
        file_name = "json_write_test"
        json_file = file_name + ".json"

        # Act
        write_json_file(JSON_DATA, file_name)

        # Assert
        with open(json_file) as reader:
            self.assertEqual(reader.read(), EXPECTED_JSON_STRING)

        # Act
        read_json_data = read_json_file(DataModel, file_name)

        # Assert
        self.assertEqual(read_json_data, JSON_DATA)

        # Cleanup
        remove(json_file)

    def test_setup_serialization(self) -> None:
        # Act
        set_serializers()

    def test_setup_deserialization(self) -> None:
        # Act
        set_deserializers()
