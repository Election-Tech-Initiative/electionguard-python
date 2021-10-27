"""
Testing tool to validate serialization and deserialization.

WARNING: Not for production use.

Specifically constructed to assist with json loading and dumping within the library.
As a secondary case, this displays how many python serializers/deserializers should be able to take
advantage of the dataclass usage.
"""

from dataclasses import asdict, is_dataclass
from enum import Enum
import json
import os
from pathlib import Path
from typing import Any, Callable, List, Optional, Type, TypeVar, Union, cast

from pydantic.json import pydantic_encoder
from pydantic.tools import parse_raw_as, parse_obj_as

from electionguard.group import hex_to_int, int_to_hex
from electionguard.group import BaseElement

T = TypeVar("T")


def construct_path(
    target_file_name: str,
    target_path: Optional[Path] = None,
    target_file_extension="json",
) -> Path:
    """Construct path from file name, path, and extension."""
    target_file = f"{target_file_name}.{target_file_extension}"
    return os.path.join(target_path, target_file)


def from_raw(type_: Type[T], obj: Any) -> T:
    """Deserialize raw as type."""
    obj = custom_decoder(obj)
    return cast(type_, parse_raw_as(type_, obj))


def to_raw(data: Any) -> Any:
    """Serialize data to raw json format."""
    return json.dumps(data, indent=4, default=custom_encoder)


def from_file_to_dataclass(dataclass_type_: Type[T], path: Union[str, Path]) -> T:
    """Deserialize file as dataclass type."""
    with open(path, "r") as json_file:
        data = json.load(json_file)
        data = custom_decoder(data)
    return parse_obj_as(dataclass_type_, data)


def from_list_in_file_to_dataclass(
    dataclass_type_: Type[T], path: Union[str, Path]
) -> T:
    """Deserialize list of objects in file as dataclass type."""
    with open(path, "r") as json_file:
        data = json.load(json_file)
        data = custom_decoder(data)
    return cast(dataclass_type_, parse_obj_as(List[dataclass_type_], data))


def to_file(
    data: Any,
    target_file_name: str,
    target_path: Optional[Path] = None,
    target_file_extension="json",
) -> None:
    """Serialize object to file (defaultly json)."""
    if not os.path.exists(target_path):
        os.makedirs(target_path)

    with open(
        construct_path(target_file_name, target_path, target_file_extension), "w"
    ) as outfile:
        json.dump(data, outfile, indent=4, default=custom_encoder)


# Color and abbreviation can both be of type hex but should not be converted
banlist = ["color", "abbreviation", "is_write_in"]


def _recursive_replace(object, type_: Type, replace: Callable[[Any], Any]):
    """Iterate through object to replace."""
    if isinstance(object, dict):
        for key, item in object.items():
            if isinstance(item, (dict, list)):
                object[key] = _recursive_replace(item, type_, replace)
            if isinstance(item, type_) and key not in banlist:
                object[key] = replace(item)
    if isinstance(object, list):
        for index, item in enumerate(object):
            if isinstance(item, (dict, list)):
                object[index] = _recursive_replace(item, type_, replace)
            if isinstance(item, type_):
                object[index] = replace(item)
    return object


class NumberEncodeOption(Enum):
    """Option for encoding numbers."""

    Default = "default"
    Hex = "hex"
    # Base64 = "base64"


OPTION = NumberEncodeOption.Hex


def _get_int_encoder() -> Callable[[Any], Any]:
    if OPTION is NumberEncodeOption.Hex:
        return int_to_hex
    return lambda x: x


def custom_encoder(obj: Any) -> Any:
    """Integer encoder to convert int representations to type for json."""
    if is_dataclass(obj):
        new_dict = asdict(obj)
        obj = _recursive_replace(new_dict, int, _get_int_encoder())
        return obj
    elif isinstance(obj, BaseElement):
        return obj.to_hex()
    return pydantic_encoder(obj)


def _get_int_decoder() -> Callable[[Any], Any]:
    def safe_hex_to_int(input: str) -> Union[int, str]:
        try:
            return hex_to_int(input)
        except ValueError:
            return input

    if OPTION is NumberEncodeOption.Hex:
        return safe_hex_to_int
    return lambda x: x


def custom_decoder(obj: Any) -> Any:
    """Integer decoder to convert json stored int back to int representations."""
    return _recursive_replace(obj, str, _get_int_decoder())
