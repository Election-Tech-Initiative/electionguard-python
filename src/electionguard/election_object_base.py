"""Base objects to derive other election objects."""

from dataclasses import dataclass
from typing import List, Sequence, TypeVar


@dataclass
class ElectionObjectBase:
    """A base object to derive other election objects identifiable by object_id."""

    object_id: str


@dataclass
class OrderedObjectBase(ElectionObjectBase):
    """A ordered base object to derive other election objects."""

    sequence_order: int
    """
    Used for ordering in a ballot to ensure various encryption primitives are deterministic.
    The sequence order must be unique and should be representative of how the items are represented
    on a template ballot in an external system.  The sequence order is not required to be in the order
    in which they are displayed to a voter.  Any acceptable range of integer values may be provided.
    """


_Orderable_T = TypeVar("_Orderable_T", bound="OrderedObjectBase")


def sequence_order_sort(unsorted: List[_Orderable_T]) -> List[_Orderable_T]:
    """Sort by sequence order."""
    return sorted(unsorted, key=lambda item: item.sequence_order)


def list_eq(
    list1: Sequence[ElectionObjectBase], list2: Sequence[ElectionObjectBase]
) -> bool:
    """
    We want to compare lists of election objects as if they're sets. We fake this by first
    sorting them on their object ids, then using regular list comparison.
    """
    return sorted(list1, key=lambda x: x.object_id) == sorted(
        list2, key=lambda x: x.object_id
    )
