from datetime import datetime, timezone
from os import mkdir, path
from re import sub
from typing import Callable, Optional, TypeVar

_T = TypeVar("_T")
_U = TypeVar("_U")


def get_optional(optional: Optional[_T]) -> _T:
    """
    General-purpose unwrapping function to handle `Optional`.
    Raises an exception if it's actually `None`, otherwise
    returns the internal type.
    """
    assert optional is not None, "Unwrap called on None"
    return optional


def match_optional(
    optional: Optional[_T], none_func: Callable[[], _U], some_func: Callable[[_T], _U]
) -> _U:
    """
    General-purpose pattern-matching function to handle `Optional`.
    If it's actually `None`, the `none_func` lambda is called.
    Otherwise, the `some_func` lambda is called with the value.
    """
    if optional is None:
        return none_func()
    return some_func(optional)


def get_or_else_optional(optional: Optional[_T], alt_value: _T) -> _T:
    """
    General-purpose getter for `Optional`. If it's `None`, returns the `alt_value`.
    Otherwise, returns the contents of `optional`.
    """
    if optional is None:
        return alt_value
    return optional


def get_or_else_optional_func(optional: Optional[_T], func: Callable[[], _T]) -> _T:
    """
    General-purpose getter for `Optional`. If it's `None`, calls the lambda `func`
    and returns its value. Otherwise, returns the contents of `optional`.
    """
    if optional is None:
        return func()
    return optional


def flatmap_optional(
    optional: Optional[_T], mapper: Callable[[_T], _U]
) -> Optional[_U]:
    """
    General-purpose flatmapping on `Optional`. If it's `None`, returns `None` as well,
    otherwise returns the lambda applied to the contents.
    """
    if optional is None:
        return None
    return mapper(optional)


def to_ticks(date_time: datetime) -> int:
    """
    Return the number of ticks for a date time.
    Ticks are defined here as number of seconds since the unix epoch (00:00:00 UTC on 1 January 1970)
    :param date_time: Date time to convert
    :return: number of ticks
    """

    ticks = (
        date_time.timestamp()
        if date_time.tzinfo
        else date_time.astimezone(timezone.utc).timestamp()
    )
    return int(ticks)


def space_between_capitals(base: str) -> str:
    """
    Return a modified string with spaces between capital letters
    :param base: base string
    :return: modified string
    """
    return sub(r"(\w)([A-Z])", r"\1 \2", base)


def make_directory(directory_path: str) -> None:
    """Create a directory only if it does not exist"""
    if not path.exists(directory_path):
        mkdir(directory_path)
