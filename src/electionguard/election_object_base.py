from dataclasses import dataclass

from .serializable import Serializable


@dataclass
class ElectionObjectBase(Serializable):
    """
    A base object to derive other election objects
    that is both serializable and identifiable by object_id
    """

    object_id: str
