from dataclasses import dataclass
from typing import cast, TypeVar, Generic

from jsons import KEY_TRANSFORMER_CAMELCASE, KEY_TRANSFORMER_SNAKECASE, dumps, loads

T = TypeVar("T")


@dataclass
class Serializable(Generic[T]):
    """
    Serializable class with methods to convert ot json
    """

    def to_json(self) -> str:
        """
        Serialize to json
        :return: the json representation of this object
        """
        return cast(
            str,
            dumps(
                self,
                strip_privates=True,
                strip_nulls=True,
                key_transformer=KEY_TRANSFORMER_CAMELCASE,
            ),
        )

    @classmethod
    def from_json(cls, data: str) -> T:
        """
        Deserialize the provided data string into the specified instance
        """
        return cast(T, loads(data, cls, key_transformer=KEY_TRANSFORMER_SNAKECASE))
