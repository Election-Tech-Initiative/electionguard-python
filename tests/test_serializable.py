from unittest import TestCase
from os import remove

from electionguard.serializable import write_json_file


class TestSerializable(TestCase):
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
