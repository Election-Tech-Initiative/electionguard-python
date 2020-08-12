from dataclasses import dataclass
from datetime import datetime
from os import path
from typing import cast, TypeVar, Generic

from jsons import (
    dumps,
    NoneType,
    loads,
    JsonsError,
    set_deserializer,
    set_serializer,
    set_validator,
    suppress_warnings,
    default_nonetype_deserializer,
)

T = TypeVar("T")

JSON_FILE_EXTENSION: str = ".json"
WRITE: str = "w"
READ: str = "r"
JSON_PARSE_ERROR = '{"error": "Object could not be parsed due to json issue"}'
# TODO Issue #??: Jsons library incorrectly dumps class method
FROM_JSON_FILE = '"from_json_file": {}, '


@dataclass
class Serializable(Generic[T]):
    """
    Serializable class with methods to convert to json
    """

    def to_json(self, strip_privates: bool = True) -> str:
        """
        Serialize to json
        :param strip_privates: strip private variables
        :return: the json representation of this object
        """
        set_serializers()
        suppress_warnings()
        try:
            return cast(
                str, dumps(self, strip_privates=strip_privates, strip_nulls=True)
            ).replace(FROM_JSON_FILE, "")
        except JsonsError:
            return JSON_PARSE_ERROR

    def to_json_file(
        self, file_name: str, file_path: str = "", strip_privates: bool = True
    ) -> None:
        """
        Serialize an object to a json file
        :param file_name: File name
        :param file_path: File path
        :param strip_privates: Strip private variables
        """
        write_json_file(self.to_json(strip_privates), file_name, file_path)

    @classmethod
    def from_json_file(cls, file_name: str, file_path: str = "") -> T:
        """
        Deserialize the provided file into the specified instance
        """
        json_file_path: str = path.join(file_path, file_name + JSON_FILE_EXTENSION)
        with open(json_file_path, READ) as json_file:
            data = json_file.read()
            target = cls.from_json(data)
        return target

    @classmethod
    def from_json(cls, data: str) -> T:
        """
        Deserialize the provided data string into the specified instance
        """
        set_deserializers()
        return cast(T, loads(data, cls))


def write_json_file(json_data: str, file_name: str, file_path: str = "") -> None:
    """
    Write json data string to json file
    """
    json_file_path: str = path.join(file_path, file_name + JSON_FILE_EXTENSION)
    with open(json_file_path, WRITE) as json_file:
        json_file.write(json_data)


def set_serializers() -> None:
    """Set serializers for jsons to use to cast specific classes"""

    # Local import to minimize jsons usage across files
    from .group import ElementModP, ElementModQ

    set_serializer(lambda p, **_: str(p), ElementModP)
    set_serializer(lambda q, **_: str(q), ElementModQ)
    set_serializer(lambda dt, **_: dt.isoformat(), datetime)


def set_deserializers() -> None:
    """Set deserializers and validators for json to use to cast specific classes"""

    # Local import to minimize jsons usage across files
    from .group import ElementModP, ElementModQ, int_to_p_unchecked, int_to_q_unchecked

    set_deserializer(
        lambda p_as_int, cls, **_: int_to_p_unchecked(p_as_int), ElementModP
    )
    set_validator(lambda p: p.is_in_bounds(), ElementModP)

    set_deserializer(
        lambda q_as_int, cls, **_: int_to_q_unchecked(q_as_int), ElementModQ
    )
    set_validator(lambda q: q.is_in_bounds(), ElementModQ)

    set_deserializer(
        lambda none, cls, **_: None
        if none == "None"
        else default_nonetype_deserializer(none),
        NoneType,
    )

    set_deserializer(lambda dt, cls, **_: datetime.fromisoformat(dt), datetime)
