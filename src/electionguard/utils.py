from datetime import datetime
from os import mkdir, path
from re import sub
from typing import Callable, Optional, TypeVar

T = TypeVar("T")
U = TypeVar("U")


def get_optional(optional: Optional[T]) -> T:
    """
    General-purpose unwrapping function to handle `Optional`.
    Raises an exception if it's actually `None`, otherwise
    returns the internal type.
    """
    assert optional is not None, "Unwrap called on None"
    return optional


def match_optional(
    optional: Optional[T], none_func: Callable[[], U], some_func: Callable[[T], U]
) -> U:
    """
    General-purpose pattern-matching function to handle `Optional`.
    If it's actually `None`, the `none_func` lambda is called.
    Otherwise, the `some_func` lambda is called with the value.
    """
    if optional is None:
        return none_func()
    else:
        return some_func(optional)


def get_or_else_optional(optional: Optional[T], alt_value: T) -> T:
    """
    General-purpose getter for `Optional`. If it's `None`, returns the `alt_value`.
    Otherwise, returns the contents of `optional`.
    """
    if optional is None:
        return alt_value
    else:
        return optional


def get_or_else_optional_func(optional: Optional[T], func: Callable[[], T]) -> T:
    """
    General-purpose getter for `Optional`. If it's `None`, calls the lambda `func`
    and returns its value. Otherwise, returns the contents of `optional`.
    """
    if optional is None:
        return func()
    else:
        return optional


def flatmap_optional(optional: Optional[T], mapper: Callable[[T], U]) -> Optional[U]:
    """
    General-purpose flatmapping on `Optional`. If it's `None`, returns `None` as well,
    otherwise returns the lambda applied to the contents.
    """
    if optional is None:
        return None
    else:
        return mapper(optional)


def to_ticks(date_time: datetime) -> int:
    """
    Return the number of ticks for a date time
    :param date_time: Date time to convert
    :return: number of ticks
    """
    t0 = datetime(1, 1, 1)
    seconds = int((date_time - t0).total_seconds())
    ticks = seconds * 10 ** 7
    return ticks


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
