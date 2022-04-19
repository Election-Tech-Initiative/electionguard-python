from datetime import datetime
from io import TextIOWrapper
import json
import os
from pathlib import Path
from typing import Any, List, Type, TypeVar, Union

from dacite import Config, from_dict
from pydantic.json import pydantic_encoder
from pydantic.tools import parse_raw_as, schema_json_of

from .ballot_box import BallotBoxState
from .manifest import ElectionType, ReportingUnitType, VoteVariationType
from .group import ElementModP, ElementModQ
from .proof import ProofUsage

_T = TypeVar("_T")

_indent = 2
_encoding = "utf-8"
_file_extension = "json"

_config = Config(
    cast=[
        datetime,
        ElementModP,
        ElementModQ,
        BallotBoxState,
        ElectionType,
        ReportingUnitType,
        VoteVariationType,
        ProofUsage,
    ],
    type_hooks={datetime: datetime.fromisoformat},
)


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


def from_file_wrapper(type_: Type[_T], file: TextIOWrapper) -> _T:
    """Deserialize json file as type."""

    data = json.load(file)
    return from_dict(type_, data, _config)


def from_file(type_: Type[_T], path: Union[str, Path]) -> _T:
    """Deserialize json file as type."""

    with open(path, "r", encoding=_encoding) as json_file:
        data = json.load(json_file)
    return from_dict(type_, data, _config)


def from_list_in_file(type_: Type[_T], path: Union[str, Path]) -> List[_T]:
    """Deserialize json file that has an array of certain type."""

    with open(path, "r", encoding=_encoding) as json_file:
        data = json.load(json_file)
        ls: List[_T] = []
        for item in data:
            ls.append(from_dict(type_, item, _config))
    return ls


def from_list_in_file_wrapper(type_: Type[_T], file: TextIOWrapper) -> List[_T]:
    """Deserialize json file that has an array of certain type."""

    data = json.load(file)
    ls: List[_T] = []
    for item in data:
        ls.append(from_dict(type_, item, _config))
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
