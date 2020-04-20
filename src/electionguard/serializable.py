from dataclasses import dataclass
from typing import TypeVar, Generic

from jsons import KEY_TRANSFORMER_SNAKECASE, dumps, loads

T = TypeVar('T')

@dataclass
class Serializable(Generic[T]):
    def to_json(self) -> str:
        """
        :return: the json representation of this object
        """
        return dumps(self.__dict__, strip_privates=True)

    @classmethod
    def from_json(cls, data: str) -> T:
        """
        deserialize the provided data string into the specified instance
        """
        return loads(data, cls, key_transformer=KEY_TRANSFORMER_SNAKECASE)
