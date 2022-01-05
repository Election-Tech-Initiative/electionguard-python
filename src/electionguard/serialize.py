import json
import os
from pathlib import Path
from typing import Any, List, Type, TypeVar, Union

from pydantic import BaseModel, PrivateAttr
from pydantic.json import pydantic_encoder
from pydantic.tools import parse_raw_as, parse_obj_as, schema_json_of

Private = PrivateAttr


class Serializable(BaseModel):
    """Serializable data object intended for exporting and importing"""

    class Config:
        """Model config to handle private properties"""

        underscore_attrs_are_private = True


_T = TypeVar("_T")

_indent = 2
_encoding = "utf-8"
_file_extension = "json"


def construct_path(
    target_file_name: str,
    target_path: str = "",
    target_file_extension: str = _file_extension,
) -> str:
    """Construct path from file name, path, and extension."""

    target_file = f"{target_file_name}.{target_file_extension}"
    return os.path.join(target_path, target_file)


def from_raw(type_: Type[_T], obj: Any) -> _T:
    """Deserialize raw as type."""

    return parse_raw_as(type_, obj)


def to_raw(data: Any) -> Any:
    """Serialize data to raw json format."""

    return json.dumps(data, indent=_indent, default=pydantic_encoder)


def from_file(type_: Type[_T], path: Union[str, Path]) -> _T:
    """Deserialize json file as type."""

    with open(path, "r", encoding=_encoding) as json_file:
        data = json.load(json_file)
    return parse_obj_as(type_, data)


def from_list_in_file(type_: Type[_T], path: Union[str, Path]) -> List[_T]:
    """Deserialize json file that has an array of certain type."""

    with open(path, "r", encoding=_encoding) as json_file:
        data = json.load(json_file)
        ls: List[_T] = []
        for item in data:
            ls.append(parse_obj_as(type_, item))
    return ls


def to_file(
    data: Any,
    target_file_name: str,
    target_path: str = "",
) -> None:
    """Serialize object to JSON"""

    if not os.path.exists(target_path):
        os.makedirs(target_path)

    with open(
        construct_path(target_file_name, target_path),
        "w",
        encoding=_encoding,
    ) as outfile:
        json.dump(data, outfile, indent=_indent, default=pydantic_encoder)


def get_schema(_type: Any) -> str:
    """Get JSON Schema for type"""

    return schema_json_of(_type)
