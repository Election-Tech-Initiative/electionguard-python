from dataclasses import dataclass
from typing import TypeVar, Generic

from jsons import JsonSerializable, KEY_TRANSFORMER_SNAKECASE, dumps, loads

T = TypeVar('T')

@dataclass
class Serializable(Generic[T]):
    """
    """
    def to_json(self) -> str:
        return dumps(self.__dict__, strip_privates=True)

    @classmethod
    def from_json(cls, data: str) -> T:
        return loads(data, cls, key_transformer=KEY_TRANSFORMER_SNAKECASE)
