from datetime import datetime, timezone
from enum import Enum
from re import sub
from typing import Callable, List, Optional, TypeVar
from base64 import b16decode

from .type import ContestId, SelectionId

_T = TypeVar("_T")
_U = TypeVar("_U")

BYTE_ORDER = "big"
BYTE_ENCODING = "utf-8"


class ContestErrorType(Enum):
    """Various errors that can occur on ballots contest after voting."""

    Default = "default"
    NullVote = "nullvote"
    UnderVote = "undervote"
    OverVote = "overvote"


class ContestException(Exception):
    """Generic contest error"""

    type: ContestErrorType

    def __init__(
        self,
        contest_id: ContestId,
        type: ContestErrorType = ContestErrorType.Default,
        override_message: Optional[str] = None,
    ):
        self.type = type
        super().__init__(
            override_message or f"{type} error has occurred on contest {contest_id}."
        )


class OverVoteException(ContestException):
    """Over vote on contest error."""

    overvoted_ids: List[SelectionId]

    def __init__(self, contest_id: ContestId, overvoted_ids: List[SelectionId]):
        self.overvoted_ids = overvoted_ids
        super().__init__(contest_id, ContestErrorType.OverVote)


class UnderVoteException(ContestException):
    """Under vote on contest error."""

    def __init__(self, contest_id: ContestId):
        super().__init__(contest_id, ContestErrorType.UnderVote)


class NullVoteException(ContestException):
    """Null vote on contest error."""

    def __init__(self, contest_id: ContestId):
        super().__init__(contest_id, ContestErrorType.NullVote)


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


def to_hex_bytes(data: bytes) -> bytes:
    """
    Convert from the element to the representation of bytes by first going through hex.
    """

    return b16decode(data)


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


def to_iso_date_string(date_time: datetime) -> str:
    """
    Return the number of ticks for a date time.
    Ticks are defined here as number of seconds since the unix epoch (00:00:00 UTC on 1 January 1970)
    :param date_time: Date time to convert
    :return: number of ticks
    """
    utc_datetime = (
        date_time.astimezone(timezone.utc).replace(microsecond=0)
        if date_time.tzinfo
        else date_time.replace(microsecond=0)
    )
    return utc_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")


def space_between_capitals(base: str) -> str:
    """
    Return a modified string with spaces between capital letters
    :param base: base string
    :return: modified string
    """
    return sub(r"(\w)([A-Z])", r"\1 \2", base)
