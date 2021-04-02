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


_T = TypeVar("_T")
_U = TypeVar("_U")


class DataStore(Generic[_T, _U]):
    """
    A lightweight convenience wrapper around a dictionary for data storage.
    This implementation defines the common interface used to access stored
    state elements.
    """

    _store: Dict[_T, _U]

    def __init__(self) -> None:
        self._store = {}

    def __iter__(self) -> Iterator:
        return iter(self._store.items())

    def all(self) -> List[_U]:
        """
        Get all `SubmittedBallot` from the store
        """
        return list(self._store.values())

    def clear(self) -> None:
        """
        Clear data from store
        """
        self._store.clear()

    def get(self, key: _T) -> Optional[_U]:
        """
        Get value in store
        :param key: key
        :return: value if found
        """
        return self._store.get(key)

    def items(self) -> Iterable[Tuple[_T, _U]]:
        """
        Gets all items in store as list
        :return: List of (key, value)
        """
        return self._store.items()

    def keys(self) -> Iterable[_T]:
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

    def pop(self, key: _T) -> Optional[_U]:
        """
        Pop an object from the store if it exists.
        :param key: key
        """
        if key in self._store:
            return self._store.pop(key)
        return None

    def set(self, key: _T, value: _U) -> None:
        """
        Create or update a new value in store
        :param key: key
        :param value: value
        """
        self._store[key] = value

    def values(self) -> Iterable[_U]:
        """
        Gets all values in store as list
        :return: List of values
        """
        return self._store.values()


class ReadOnlyDataStore(Generic[_T, _U], Mapping):
    """
    A readonly view to a Data store
    """

    def __init__(self, data: DataStore[_T, _U]):
        self._data: DataStore[_T, _U] = data

    def __getitem__(self, key: _T) -> Optional[_U]:
        return self._data.get(key)

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator:
        return iter(self._data.items())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ReadOnlyDataStore):
            return False
        return ReadOnlyDataStore.__eq__(self, other)
