from collections.abc import Mapping

from typing import (
    Dict,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
    TypeVar,
)


T = TypeVar("T")
U = TypeVar("U")


class DataStore(Generic[T, U], Iterable):
    """
    A lightweight convenience wrapper around a dictionary for data storage.
    This implementation defines the common interface used to access stored
    state elements.  
    """

    _store: Dict[T, U]

    def __init__(self) -> None:
        self._store = {}

    def __iter__(self) -> Iterator:
        return iter(self._store.items())

    def all(self) -> List[Optional[U]]:
        """
        Get all `CiphertextAcceptedBallot` from the store
        """
        return list(self._store.values())

    def clear(self) -> None:
        """
        Clear data from store
        """
        self._store.clear()

    def get(self, key: T) -> Optional[U]:
        """
        Get value in store
        :param key: key
        :return: value if found
        """
        return self._store.get(key)

    def items(self) -> Iterable[Tuple[T, U]]:
        """
        Gets all items in store as list
        :return: List of (key, value)
        """
        return self._store.items()

    def keys(self) -> Iterable[T]:
        """
        Gets all keys in store as list
        :return: List of keys
        """
        return self._store.keys()

    def __len__(self) -> int:
        """
        Get length or count of store
        :return: Count in store
        """
        return len(self._store)

    def pop(self, key: T) -> Optional[U]:
        """
        Pop an object from the store if it exists.
        :param key: key
        """
        if key in self._store:
            return self._store.pop(key)
        return None

    def set(self, key: T, value: U) -> None:
        """
        Create or update a new value in store
        :param key: key
        :param value: value
        """
        self._store[key] = value

    def values(self) -> Iterable[U]:
        """
        Gets all values in store as list
        :return: List of values
        """
        return self._store.values()


class ReadOnlyDataStore(Generic[T, U], Mapping):
    """
    A readonly view to a Data store
    """

    def __init__(self, data: DataStore[T, U]):
        self._data: DataStore[T, U] = data

    def __getitem__(self, key: T) -> Optional[U]:
        return self._data.get(key)

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator:
        return iter(self._data.items())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ReadOnlyDataStore):
            return False
        return ReadOnlyDataStore.__eq__(self, other)
