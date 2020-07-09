from dataclasses import dataclass
from jsons import (
    KEY_TRANSFORMER_CAMELCASE,
    KEY_TRANSFORMER_SNAKECASE,
    dumps,
    loads,
    JsonsError,
)
from typing import cast, TypeVar, Generic

T = TypeVar("T")

JSON_FILE_EXTENSION: str = ".json"
WRITE: str = "w"
JSON_PARSE_ERROR = '{"error": "Object could not be parsed due to json issue"}'

# base10 as string for ElementModP and ElementModQ


@dataclass
class Serializable(Generic[T]):
    """
    Serializable class with methods to convert to json
    """

    def to_json(self) -> str:
        """
        Serialize to json
        :return: the json representation of this object
        """
        try:
            return cast(
                str,
                dumps(
                    self,
                    strip_privates=True,
                    strip_nulls=True,
                    key_transformer=KEY_TRANSFORMER_CAMELCASE,
                ),
            )
        except JsonsError:
            return JSON_PARSE_ERROR

    def to_json_file(self, file_name: str, file_path: str = "") -> None:
        """
        Serialize an object to a json file
        """
        write_json_file(self.to_json(), file_name, file_path)

    @classmethod
    def from_json(cls, data: str) -> T:
        """
        Deserialize the provided data string into the specified instance
        """
        return cast(T, loads(data, cls, key_transformer=KEY_TRANSFORMER_SNAKECASE))


def write_json_file(json_data: str, file_name: str, file_path: str = "") -> None:
    """
    Write json data string to json file
    """
    json_file_path: str = file_path + file_name + JSON_FILE_EXTENSION
    with open(json_file_path, WRITE) as json_file:
        json_file.write(json_data)
