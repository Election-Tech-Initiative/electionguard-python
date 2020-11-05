from typing import Any
from os.path import join, dirname, realpath
from json import load
from jsonschema import validate
from jsonschema.exceptions import ValidationError

__all__ = ["election_description_schema", "validate_json_schema"]


def _load_schema(json_schema_file_name: str) -> Any:
    """Loads the given schema"""
    with open(join(dirname(realpath(__file__)), json_schema_file_name), "r") as file:
        schema = load(file)
    return schema


election_description_schema = _load_schema("election_description_schema.json")


def validate_json_schema(
    json_data: Any,
    json_schema: Any,
) -> bool:
    """Validate json schema"""
    try:
        validate(instance=json_data, schema=json_schema)
    except ValidationError as err:
        return False
    return True
